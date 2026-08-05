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
    CargaHora,
    ClimaHora,
    Equipamento,
    FaturaHora,
    FazendaSpec,
    GeracaoHora,
    Gerador,
    OverrideSpec,
    SimResult,
    TarifaHora,
)


def _serie_geracao(
    fazenda: FazendaSpec,
    geradores: Mapping[str, Gerador],
    clima: Sequence[ClimaHora],
    detalhado: bool,
) -> tuple[list[float], list[GeracaoHora]]:
    ativos = [
        geradores[gid]
        for gid in (fazenda.id_solar, fazenda.id_eolica)
        if gid is not None and gid in geradores
    ]
    total = [0.0] * len(clima)
    detalhe: list[GeracaoHora] = []
    for g in ativos:
        for i, c in enumerate(clima):
            energia = gerar_hora(c, g)
            total[i] += energia
            if detalhado:
                detalhe.append(
                    GeracaoHora(
                        id_fazenda=fazenda.id,
                        data_hora=c.data_hora,
                        mes=c.mes,
                        hora=c.hora,
                        gerador_id=g.id,
                        tipo=g.tipo,
                        energia_kwh=energia,
                    )
                )
    return total, detalhe


def simular_fazenda(
    fazenda: FazendaSpec,
    equipamentos: Sequence[Equipamento],
    geradores: Mapping[str, Gerador],
    tarifa: Sequence[TarifaHora],
    clima: Sequence[ClimaHora],
    overrides: Sequence[OverrideSpec] = (),
    detalhado: bool = False,
) -> SimResult:
    n = len(clima)

    # 0. Resolve o catálogo para a fazenda (porte + overrides do cadastro personalizado).
    resolvidos = resolver_equipamentos(equipamentos, fazenda.porte, overrides)

    # 1. Cargas instanciadas (+ bateria), reusando os perfis para o consumo.
    perfis = perfis_por_carga(resolvidos)
    cargas = cargas_from_perfis(fazenda, perfis)

    # 2. Geração horária (total + detalhe por gerador se detalhado).
    geracao, geracao_horaria = _serie_geracao(fazenda, geradores, clima, detalhado)

    # 3. Consumo horário total (soma das cargas não-armazenamento).
    consumo_total = [0.0] * n
    cargas_horarias: list[CargaHora] = []
    for idx, ((_load, perfil), carga) in enumerate(zip(perfis, cargas, strict=False)):
        serie = consumo_serie(carga, idx, perfil, clima, fazenda.seed, fazenda.ano)
        for i in range(n):
            consumo_total[i] += serie[i]
            if detalhado:
                c = clima[i]
                cargas_horarias.append(
                    CargaHora(
                        id_fazenda=fazenda.id,
                        data_hora=c.data_hora,
                        mes=c.mes,
                        hora=c.hora,
                        carga=carga.carga,
                        tipo=carga.tipo,
                        consumo_kwh=serie[i],
                    )
                )

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
        fazenda_id=fazenda.id,
        cargas=cargas,
        fatura=fatura,
        resumo=resumo,
        ranking=ranking,
        equipamentos=list(resolvidos),
        cargas_horarias=cargas_horarias,
        geracao_horaria=geracao_horaria,
    )
