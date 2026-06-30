"""Geração solar/eólica — valores determinísticos validados contra a planilha."""

import pytest

from fems.data.catalog_seed import GERADORES
from fems.domain.simulation.geracao import gerar_eolica, gerar_solar

GER = {g.id: g for g in GERADORES}


def test_solar_noon_matches_baseline():
    # SOL-PEQ, 1º jan 12h: GHI=1071.8, FP=0.95 -> 7.867986364 (célula Geracao da v8)
    assert gerar_solar(1071.8, 0.95, GER["SOL-PEQ"]) == pytest.approx(7.867986364, abs=1e-6)


def test_solar_cutoff_below_gen_min_returns_zero():
    # h05 GHI=15.3 -> raw < Gen_Min(0.5) -> 0 (planilha mostra 0)
    assert gerar_solar(15.3, 0.95, GER["SOL-PEQ"]) == 0.0


def test_solar_clamped_at_gen_max():
    assert gerar_solar(5000.0, 1.0, GER["SOL-PEQ"]) == GER["SOL-PEQ"].gen_max_kw


def test_solar_zero_at_night():
    assert gerar_solar(0.0, 0.95, GER["SOL-PEQ"]) == 0.0


def test_eolica_h00_matches_baseline():
    # EOL-PEQ, 1º jan 00h: vento=4.32, FP=0.95 -> 1.04652
    assert gerar_eolica(4.32, 0.95, GER["EOL-PEQ"]) == pytest.approx(1.04652, abs=1e-9)


def test_eolica_normalizacao_clamp_em_1():
    # vento muito alto -> vento_norm satura em 1*FP; não é curva cúbica
    eol = GER["EOL-MED"]  # kwp=10, efic=87, ref=10, max=10, min=0.3
    # vento=100 -> min(1,10)*1.0=1.0 ; raw=1.0*10*0.87=8.7 ; <=max
    assert gerar_eolica(100.0, 1.0, eol) == pytest.approx(8.7, abs=1e-9)
