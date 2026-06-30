"""Agregação mensal por fazenda (aba `Resumo_Mensal`)."""

from __future__ import annotations

from collections.abc import Sequence

from fems.domain.configuration.enums import TipoHorario
from fems.domain.simulation.types import FaturaHora, ResumoMes


def resumo_mensal(id_fazenda: str, fatura: Sequence[FaturaHora]) -> list[ResumoMes]:
    consumo: dict[int, float] = {}
    geracao: dict[int, float] = {}
    custo_total: dict[int, float] = {}
    custo_ponta: dict[int, float] = {}
    bateria: dict[int, float] = {}
    saldo_liquido: dict[int, float] = {}

    for f in fatura:
        m = f.mes
        consumo[m] = consumo.get(m, 0.0) + f.consumo_kwh
        geracao[m] = geracao.get(m, 0.0) + f.geracao_kwh
        custo_total[m] = custo_total.get(m, 0.0) + f.custo_rs
        if f.tipo_horario == TipoHorario.PONTA:
            custo_ponta[m] = custo_ponta.get(m, 0.0) + f.custo_rs
        bateria[m] = bateria.get(m, 0.0) + f.bateria_descarga_kwh
        saldo_liquido[m] = saldo_liquido.get(m, 0.0) + f.saldo_liquido_kwh

    resumos: list[ResumoMes] = []
    for m in sorted(consumo):
        total = custo_total.get(m, 0.0)
        ponta = custo_ponta.get(m, 0.0)
        resumos.append(
            ResumoMes(
                id_fazenda=id_fazenda,
                mes=m,
                consumo_kwh=consumo[m],
                geracao_kwh=geracao[m],
                saldo_rede_kwh=consumo[m] - geracao[m],
                custo_total_rs=total,
                custo_ponta_rs=ponta,
                custo_fora_ponta_rs=total - ponta,
                bateria_descarga_kwh=bateria.get(m, 0.0),
                saldo_liquido_kwh=saldo_liquido.get(m, 0.0),
            )
        )
    return resumos
