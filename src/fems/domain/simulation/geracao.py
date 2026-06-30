"""Geração solar e eólica — estrutura normalizada idêntica (clima → energia).

Solar:  raw = (GHI / Ref) * FP * kWp * (Efic% / 100)
Eólica: raw = MIN(1, Vento / Ref) * FP * kWp * (Efic% / 100)   (MESMA estrutura, não cúbica)
Energia = 0 se raw < Gen_Min; senão MIN(Gen_Max, MAX(Gen_Min, raw)).
"""

from __future__ import annotations

from fems.domain.configuration.enums import TipoGeracao
from fems.domain.simulation.types import ClimaHora, Gerador


def _clamp(raw: float, gen_min: float, gen_max: float) -> float:
    if raw < gen_min:
        return 0.0
    return min(gen_max, max(gen_min, raw))


def gerar_solar(ghi: float, fp: float, g: Gerador) -> float:
    raw = (ghi / g.ref_conversao) * fp * g.pot_nominal_kwp * (g.eficiencia_pct / 100.0)
    return _clamp(raw, g.gen_min_kw, g.gen_max_kw)


def gerar_eolica(vento: float, fp: float, g: Gerador) -> float:
    vento_norm = min(1.0, vento / g.ref_conversao) * fp
    raw = vento_norm * g.pot_nominal_kwp * (g.eficiencia_pct / 100.0)
    return _clamp(raw, g.gen_min_kw, g.gen_max_kw)


def gerar_hora(clima: ClimaHora, g: Gerador) -> float:
    if g.tipo == TipoGeracao.SOLAR_FV:
        return gerar_solar(clima.ghi, clima.fp, g)
    return gerar_eolica(clima.vento, clima.fp, g)
