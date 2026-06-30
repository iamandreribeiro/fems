"""Montagem da linha de fatura horária (aba `Consumo_Fatura`).

Saldo_Rede   = Consumo - Geração
Saldo_Liquido = MAX(0, Consumo - Geração - Bateria_Descarga)
Custo        = Saldo_Liquido * Tarifa   (usa o saldo líquido, já abatida a bateria)
"""

from __future__ import annotations

from fems.domain.simulation.types import ClimaHora, FaturaHora, TarifaHora


def linha_fatura(
    id_fazenda: str,
    clima: ClimaHora,
    consumo: float,
    geracao: float,
    tarifa: TarifaHora,
    bateria_descarga: float,
) -> FaturaHora:
    saldo_rede = consumo - geracao
    saldo_liquido = max(0.0, consumo - geracao - bateria_descarga)
    custo = saldo_liquido * tarifa.preco_kwh
    return FaturaHora(
        id_fazenda=id_fazenda,
        data_hora=clima.data_hora,
        mes=clima.mes,
        hora=clima.hora,
        consumo_kwh=consumo,
        geracao_kwh=geracao,
        saldo_rede_kwh=saldo_rede,
        tarifa_rs=tarifa.preco_kwh,
        custo_rs=custo,
        tipo_horario=tarifa.tipo,
        bateria_descarga_kwh=bateria_descarga,
        saldo_liquido_kwh=saldo_liquido,
    )
