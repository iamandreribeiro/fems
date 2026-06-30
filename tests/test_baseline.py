"""Validação do motor completo contra o baseline de JANEIRO da planilha v8.

Determinístico (geração/bateria) deve bater exato; consumo (ruído com seed) é
validado por agregado mensal dentro de tolerância. A planilha v8 só populou
janeiro a jusante, então comparamos a fatia dos 744 h de janeiro.
"""

import pytest

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL
from fems.data.clima import carregar_clima
from fems.domain.configuration.enums import Porte
from fems.domain.simulation.engine import simular_fazenda
from fems.domain.simulation.types import FazendaSpec

FAZENDAS = {
    "FAZ-001": FazendaSpec(
        id="FAZ-001",
        nome="Fazenda Boa Vista",
        tamanho_ha=80.0,
        porte=Porte.PEQUENA,
        tem_escritorio=True,
        tem_cozinha=True,
        tem_quarto=True,
        tem_irrigacao=True,
        id_solar="SOL-PEQ",
        id_eolica="EOL-PEQ",
        id_bateria="BAT-001",
        tarifa="AZUL_HOROSSAZONAL",
        seed=20250101,
        ano=2025,
    ),
    "FAZ-002": FazendaSpec(
        id="FAZ-002",
        nome="Fazenda São Pedro",
        tamanho_ha=320.0,
        porte=Porte.MEDIA,
        tem_escritorio=True,
        tem_cozinha=True,
        tem_quarto=True,
        tem_irrigacao=True,
        id_solar="SOL-MED",
        id_eolica="EOL-MED",
        id_bateria="BAT-001",
        tarifa="AZUL_HOROSSAZONAL",
        seed=20250101,
        ano=2025,
    ),
}

# Resumo_Mensal (janeiro) da planilha v8
BASELINE_JAN = {
    "FAZ-001": {"consumo": 2315.19752, "geracao": 2244.029653, "bateria": 81.375},
    "FAZ-002": {"consumo": 10091.67166, "geracao": 8752.801051, "bateria": 325.5},
}


@pytest.fixture(scope="module")
def clima():
    return carregar_clima(2025)


@pytest.fixture(scope="module")
def geradores():
    return {g.id: g for g in GERADORES}


def _simular(faz_id, clima, geradores):
    return simular_fazenda(FAZENDAS[faz_id], EQUIPAMENTOS, geradores, TARIFA_AZUL, clima)


def _janeiro(result):
    return [f for f in result.fatura if f.mes == 1]


@pytest.mark.parametrize("faz_id", ["FAZ-001", "FAZ-002"])
def test_geracao_janeiro_exata(faz_id, clima, geradores):
    jan = _janeiro(_simular(faz_id, clima, geradores))
    total = sum(f.geracao_kwh for f in jan)
    assert total == pytest.approx(BASELINE_JAN[faz_id]["geracao"], abs=1e-2)


@pytest.mark.parametrize("faz_id", ["FAZ-001", "FAZ-002"])
def test_bateria_janeiro_exata(faz_id, clima, geradores):
    jan = _janeiro(_simular(faz_id, clima, geradores))
    total = sum(f.bateria_descarga_kwh for f in jan)
    assert total == pytest.approx(BASELINE_JAN[faz_id]["bateria"], abs=1e-6)


@pytest.mark.parametrize("faz_id", ["FAZ-001", "FAZ-002"])
def test_consumo_janeiro_dentro_de_3pct(faz_id, clima, geradores):
    jan = _janeiro(_simular(faz_id, clima, geradores))
    total = sum(f.consumo_kwh for f in jan)
    esperado = BASELINE_JAN[faz_id]["consumo"]
    assert total == pytest.approx(esperado, rel=0.03)


def test_serie_completa_8760_e_invariantes(clima, geradores):
    result = _simular("FAZ-001", clima, geradores)
    assert len(result.fatura) == 8760
    assert len(result.resumo) == 12
    assert all(f.consumo_kwh >= 0.0 for f in result.fatura)
    assert all(f.saldo_liquido_kwh >= 0.0 for f in result.fatura)
    assert all(f.custo_rs >= 0.0 for f in result.fatura)


def test_reprodutibilidade(clima, geradores):
    a = _simular("FAZ-001", clima, geradores)
    b = _simular("FAZ-001", clima, geradores)
    assert [f.consumo_kwh for f in a.fatura] == [f.consumo_kwh for f in b.fatura]
