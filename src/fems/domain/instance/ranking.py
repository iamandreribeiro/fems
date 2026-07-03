"""Ranking de "equipamentos que mais gastam", separado por área.

Métrica = footprint energético nominal do equipamento (independe do clamp por carga
da simulação): `kwh_dia = potencia_kw * qtd * Σ_h perfil[h]`; custo análogo ponderado
pela tarifa horária. Por área (Escritório/Cozinha/Quarto/Irrigação) ordena desc por
kWh/ano — assim os equipamentos residenciais aparecem mesmo competindo com a irrigação.
"""

from __future__ import annotations

from collections.abc import Sequence

from fems.domain.configuration.enums import Area
from fems.domain.simulation.types import EquipamentoResolvido, RankingItem, TarifaHora

DIAS_ANO_PADRAO = 365


def ranking_por_area(
    equipamentos: Sequence[EquipamentoResolvido],
    tarifa: Sequence[TarifaHora],
    dias: int = DIAS_ANO_PADRAO,
) -> dict[Area, list[RankingItem]]:
    preco = {t.hora: t.preco_kwh for t in tarifa}

    bruto: dict[Area, list[tuple[EquipamentoResolvido, float, float]]] = {}
    for e in equipamentos:
        energia_dia = e.potencia_kw * e.qtd * sum(e.perfil)
        custo_dia = e.potencia_kw * e.qtd * sum(e.perfil[h] * preco.get(h, 0.0) for h in range(24))
        kwh_ano = energia_dia * dias
        custo_ano = custo_dia * dias
        bruto.setdefault(e.area, []).append((e, kwh_ano, custo_ano))

    ranking: dict[Area, list[RankingItem]] = {}
    for area, itens in bruto.items():
        total = sum(kwh for _, kwh, _ in itens) or 1.0
        ordenados = sorted(itens, key=lambda t: t[1], reverse=True)
        ranking[area] = [
            RankingItem(
                area=area,
                equipamento_id=e.id,
                equipamento=e.equipamento,
                kwh_ano=kwh_ano,
                pct_area=100.0 * kwh_ano / total,
                custo_ano=custo_ano,
            )
            for e, kwh_ano, custo_ano in ordenados
        ]
    return ranking
