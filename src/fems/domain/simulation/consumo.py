"""Consumo horário por carga (aba `Cargas`).

Consumo = IF(Cons_Max=0, 0, IF(perfil_hora=0, 0,
              MIN(Cons_Max, MAX(Cons_Min, perfil_hora * ruído))))

`perfil_hora` é o valor de Perfil_Area daquela hora (pode exceder Cons_Max → clamp).
O ruído vem do PRNG com seed. Cargas inativas (flag de área desligada) não consomem
— implementa o "filtrar por áreas ativas" do design doc; nas fazendas de referência
todas as áreas estão ativas, então o baseline é preservado.
"""

from __future__ import annotations

from collections.abc import Sequence

from fems.domain.configuration.enums import StatusCarga
from fems.domain.simulation.prng import noise_series
from fems.domain.simulation.types import CargaInstanciada, ClimaHora


def consumo_hora(cons_max: float, cons_min: float, perfil_hora: float, ruido: float) -> float:
    if cons_max == 0.0 or perfil_hora == 0.0:
        return 0.0
    return min(cons_max, max(cons_min, perfil_hora * ruido))


def consumo_serie(
    carga: CargaInstanciada,
    carga_idx: int,
    perfil_24: tuple[float, ...],
    clima: Sequence[ClimaHora],
    seed: int,
    ano: int,
) -> list[float]:
    """Série de consumo horário (kWh) para uma carga ao longo do ano."""
    n = len(clima)
    if carga.status != StatusCarga.ATIVO or carga.cons_max_kw == 0.0:
        return [0.0] * n
    ruido = noise_series(seed, ano, carga_idx, n)
    return [
        consumo_hora(carga.cons_max_kw, carga.cons_min_kw, perfil_24[c.hora], float(ruido[i]))
        for i, c in enumerate(clima)
    ]
