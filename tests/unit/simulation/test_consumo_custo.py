"""Consumo, bateria, custo e resumo — regras determinísticas."""

from datetime import datetime

import pytest

from fems.domain.configuration.enums import StatusCarga, TipoCarga, TipoHorario
from fems.domain.simulation.bateria import descarga_bateria
from fems.domain.simulation.consumo import consumo_hora, consumo_serie
from fems.domain.simulation.custo import linha_fatura
from fems.domain.simulation.resumo import resumo_mensal
from fems.domain.simulation.types import CargaInstanciada, ClimaHora, FaturaHora, TarifaHora


def _clima(i, mes, hora):
    return ClimaHora(
        indice=i,
        data_hora=datetime(2025, mes, 1, hora),
        mes=mes,
        hora=hora,
        ghi=0.0,
        temp=25.0,
        vento=3.0,
        fp=0.95,
    )


def test_consumo_clamp_no_cons_max():
    # perfil*ruído acima do Cons_Max -> limitado ao Cons_Max
    assert consumo_hora(0.354, 0.1062, 1.714, 1.15) == 0.354


def test_consumo_piso_no_cons_min():
    assert consumo_hora(2.0, 0.6, 1.0, 0.5) == 0.6  # max(0.6, 0.5)


def test_consumo_zero_se_perfil_zero():
    assert consumo_hora(2.0, 0.6, 0.0, 1.0) == 0.0


def test_consumo_zero_se_cons_max_zero():
    assert consumo_hora(0.0, 0.0, 1.0, 1.0) == 0.0


def test_consumo_serie_reprodutivel_e_inativo_zera():
    carga = CargaInstanciada("Cozinha", TipoCarga.SEDE, 0.354, 0.1062, StatusCarga.ATIVO)
    perfil = tuple([0.274] * 24)
    clima = [_clima(i, 1, i % 24) for i in range(48)]
    a = consumo_serie(carga, 5, perfil, clima, seed=42, ano=2025)
    b = consumo_serie(carga, 5, perfil, clima, seed=42, ano=2025)
    assert a == b
    assert all(0.0 <= x <= 0.354 for x in a)

    inativa = CargaInstanciada("Cozinha", TipoCarga.SEDE, 0.354, 0.1062, StatusCarga.INATIVO)
    assert consumo_serie(inativa, 5, perfil, clima, seed=42, ano=2025) == [0.0] * 48


def test_descarga_bateria_so_na_ponta():
    assert descarga_bateria(TipoHorario.PONTA, 0.875) == 0.875
    assert descarga_bateria(TipoHorario.FORA_PONTA, 0.875) == 0.0


def test_linha_fatura_saldo_liquido_e_custo():
    th = TarifaHora(20, 1.1039, TipoHorario.PONTA)
    f = linha_fatura("FAZ-001", _clima(0, 1, 20), 4.84174, 0.663765, th, 0.875)
    assert f.saldo_liquido_kwh == pytest.approx(3.302975, abs=1e-9)
    assert f.custo_rs == pytest.approx(3.302975 * 1.1039, abs=1e-9)


def test_linha_fatura_saldo_negativo_zera_custo():
    th = TarifaHora(18, 1.1039, TipoHorario.PONTA)
    f = linha_fatura("FAZ-001", _clima(0, 1, 18), 1.312, 2.170633, th, 0.875)
    assert f.saldo_liquido_kwh == 0.0
    assert f.custo_rs == 0.0


def test_resumo_mensal_split_ponta():
    fatura = [
        FaturaHora(
            "F",
            datetime(2025, 1, 1, 10),
            1,
            10,
            5.0,
            1.0,
            4.0,
            0.6813,
            2.7252,
            TipoHorario.FORA_PONTA,
            0.0,
            4.0,
        ),
        FaturaHora(
            "F",
            datetime(2025, 1, 1, 18),
            1,
            18,
            3.0,
            1.0,
            2.0,
            1.1039,
            1.1039,
            TipoHorario.PONTA,
            0.875,
            1.0,
        ),
        FaturaHora(
            "F",
            datetime(2025, 2, 1, 10),
            2,
            10,
            2.0,
            0.0,
            2.0,
            0.6813,
            1.3626,
            TipoHorario.FORA_PONTA,
            0.0,
            2.0,
        ),
    ]
    resumo = {r.mes: r for r in resumo_mensal("F", fatura)}
    assert set(resumo) == {1, 2}
    jan = resumo[1]
    assert jan.consumo_kwh == pytest.approx(8.0)
    assert jan.custo_total_rs == pytest.approx(2.7252 + 1.1039)
    assert jan.custo_ponta_rs == pytest.approx(1.1039)
    assert jan.custo_fora_ponta_rs == pytest.approx(2.7252)
    assert jan.bateria_descarga_kwh == pytest.approx(0.875)
