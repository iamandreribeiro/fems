"""Perfil_Area + instanciação de cargas — validados contra Cadastro_Cargas da v8."""

import pytest

from fems.data.catalog_seed import EQUIPAMENTOS
from fems.domain.configuration.enums import Porte, StatusCarga
from fems.domain.instance.instanciar import (
    capacidade_bateria,
    cons_max_from_perfil,
    instanciar_cargas,
)
from fems.domain.instance.perfil_area import LOAD_DEFS, perfil_area_24h
from fems.domain.instance.resolver import resolver_equipamentos
from fems.domain.simulation.types import FazendaSpec


def _faz(porte, **flags):
    base = {
        "tem_escritorio": True,
        "tem_cozinha": True,
        "tem_quarto": True,
        "tem_irrigacao": True,
    }
    base.update(flags)
    return FazendaSpec(
        id="FAZ-X",
        nome="x",
        tamanho_ha=80.0,
        porte=porte,
        id_solar="SOL-PEQ",
        id_eolica="EOL-PEQ",
        id_bateria="BAT-001",
        tarifa="AZUL_HOROSSAZONAL",
        seed=1,
        ano=2025,
        **base,
    )


def _load(carga):
    return next(ld for ld in LOAD_DEFS if ld.carga == carga)


def test_perfil_area_escritorio_pequena():
    resolvidos = resolver_equipamentos(EQUIPAMENTOS, Porte.PEQUENA)
    perfil = perfil_area_24h(resolvidos, _load("Escritório"))
    assert perfil[0] == pytest.approx(0.02)
    assert perfil[9] == pytest.approx(2.02)  # pico diurno


def test_perfil_area_cozinha_pico_vs_h11():
    resolvidos = resolver_equipamentos(EQUIPAMENTOS, Porte.PEQUENA)
    perfil = perfil_area_24h(resolvidos, _load("Cozinha"))
    assert perfil[6] == pytest.approx(1.714)  # pico real às 06h
    assert perfil[11] == pytest.approx(0.354)  # mas Cons_Max usa a hora 11


def test_cons_max_usa_apenas_horas_0_1_11():
    # só as horas 0, 1 e 11 contam — picos em outras horas são ignorados
    perfil = tuple([0.1, 0.2] + [9.0] * 9 + [0.354] + [9.0] * 12)  # pico 9.0 fora; h11=0.354
    assert cons_max_from_perfil(perfil) == pytest.approx(0.354)
    perfil2 = tuple([5.0, 1.0] + [0.0] * 9 + [0.0] + [0.0] * 12)  # h0=5 vence
    assert cons_max_from_perfil(perfil2) == pytest.approx(5.0)


def test_capacidade_bateria_arredonda_multiplo_5():
    assert capacidade_bateria(6.75) == 5.0  # FAZ-001 (Pequena)
    assert capacidade_bateria(32.742013373) == 20.0  # FAZ-002 (Média)


def test_instanciar_faz001_pequena():
    cargas = {c.carga: c for c in instanciar_cargas(_faz(Porte.PEQUENA), EQUIPAMENTOS)}
    assert cargas["Pivô"].cons_max_kw == pytest.approx(4.0)
    assert cargas["Pivô"].cons_min_kw == pytest.approx(1.2)
    assert cargas["Cozinha"].cons_max_kw == pytest.approx(0.354)
    assert cargas["Quarto"].cons_max_kw == pytest.approx(0.176)
    assert cargas["Bateria"].cons_max_kw == 5.0
    assert cargas["Bateria"].cons_min_kw == pytest.approx(0.875)
    # Bomba/Secadora têm Qtd_Peq=0 -> Cons_Max 0 -> Inativo
    assert cargas["Bomba_Aux"].status == StatusCarga.INATIVO
    assert cargas["Secadora"].status == StatusCarga.INATIVO


def test_instanciar_faz002_media():
    cargas = {c.carga: c for c in instanciar_cargas(_faz(Porte.MEDIA), EQUIPAMENTOS)}
    assert cargas["Bomba_Aux"].cons_max_kw == pytest.approx(17.6)
    assert cargas["Secadora"].cons_max_kw == pytest.approx(2.367013373)
    assert cargas["Bateria"].cons_max_kw == 20.0


def test_flag_de_area_desligada_inativa_carga():
    cargas = {
        c.carga: c for c in instanciar_cargas(_faz(Porte.PEQUENA, tem_cozinha=False), EQUIPAMENTOS)
    }
    assert cargas["Cozinha"].status == StatusCarga.INATIVO
    # Cons_Max permanece derivado do perfil (independe da flag)
    assert cargas["Cozinha"].cons_max_kw == pytest.approx(0.354)
