"""Motor de simulação — ponto único de reuso (CLI e API chamam `simular_fazenda`).

Recebe a fazenda (paramétrica) + catálogo + clima e produz a série horária completa
e o resumo mensal. Determinístico dado (fazenda + catálogo + clima + seed).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from fems.domain.configuration.enums import TipoCarga
from fems.domain.instance.instanciar import cargas_from_perfis
from fems.domain.instance.perfil_area import perfis_por_carga
from fems.domain.instance.ranking import ranking_por_area
from fems.domain.instance.resolver import resolver_equipamentos
from fems.domain.simulation.bateria import descarga_bateria
from fems.domain.simulation.consumo import consumo_serie
from fems.domain.simulation.custo import linha_fatura
from fems.domain.simulation.geracao import gerar_hora
from fems.domain.simulation.resumo import resumo_mensal
from fems.domain.simulation.types import (
    ClimaHora,
    Equipamento,
    FaturaHora,
    FazendaSpec,
    Gerador,
    OverrideSpec,
    SimResult,
    TarifaHora,
)


def _serie_geracao(
    fazenda: FazendaSpec, geradores: Mapping[str, Gerador], clima: Sequence[ClimaHora]
) -> list[float]:
    solar = geradores.get(fazenda.id_solar) if fazenda.id_solar else None
    eolica = geradores.get(fazenda.id_eolica) if fazenda.id_eolica else None
    serie: list[float] = []
    for c in clima:
        total = 0.0
        if solar is not None:
            total += gerar_hora(c, solar)
        if eolica is not None:
            total += gerar_hora(c, eolica)
        serie.append(total)
    return serie


def simular_fazenda(
    fazenda: FazendaSpec,
    equipamentos: Sequence[Equipamento],
    geradores: Mapping[str, Gerador],
    tarifa: Sequence[TarifaHora],
    clima: Sequence[ClimaHora],
    overrides: Sequence[OverrideSpec] = (),
) -> SimResult:
    n = len(clima)

    # 0. Resolve o catálogo para a fazenda (porte + overrides do cadastro personalizado).
    resolvidos = resolver_equipamentos(equipamentos, fazenda.porte, overrides)

    # 1. Cargas instanciadas (+ bateria), reusando os perfis para o consumo.
    perfis = perfis_por_carga(resolvidos)
    cargas = cargas_from_perfis(fazenda, perfis)

    # 2. Geração horária.
    geracao = _serie_geracao(fazenda, geradores, clima)

    # 3. Consumo horário total (soma das cargas não-armazenamento).
    consumo_total = [0.0] * n
    for idx, ((_load, perfil), carga) in enumerate(zip(perfis, cargas, strict=False)):
        serie = consumo_serie(carga, idx, perfil, clima, fazenda.seed, fazenda.ano)
        for i in range(n):
            consumo_total[i] += serie[i]

    # 4. Bateria: descarrega Cons_Min cheio por hora de ponta.
    bateria = next((c for c in cargas if c.tipo == TipoCarga.ARMAZENAMENTO), None)
    descarga_kw = bateria.cons_min_kw if bateria is not None else 0.0

    # 5. Fatura horária.
    tarifa_por_hora = {t.hora: t for t in tarifa}
    fatura: list[FaturaHora] = []
    for i, c in enumerate(clima):
        th = tarifa_por_hora[c.hora]
        desc = descarga_bateria(th.tipo, descarga_kw)
        fatura.append(linha_fatura(fazenda.id, c, consumo_total[i], geracao[i], th, desc))

    # 6. Resumo mensal.
    resumo = resumo_mensal(fazenda.id, fatura)

    # 7. Ranking de equipamentos por área (footprint nominal * dias do ano).
    dias = max(1, n // 24)
    ranking = ranking_por_area(resolvidos, tarifa, dias)

    return SimResult(
        fazenda_id=fazenda.id, cargas=cargas, fatura=fatura, resumo=resumo, ranking=ranking
    )
