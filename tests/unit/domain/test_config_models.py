"""Validação dos modelos Pydantic da camada de configuração."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from fems.domain.configuration.enums import Area, TipoGeracao, TipoHorario
from fems.domain.configuration.equipamento import EquipamentoCreate
from fems.domain.configuration.geracao import ConfiguracaoGeracaoCreate
from fems.domain.configuration.tarifa import TarifaCreate, TarifaHoraCreate

PERFIL_OK = [0.0] * 24


def test_equipamento_valido():
    e = EquipamentoCreate(
        id="ESC-01",
        area=Area.ESCRITORIO,
        equipamento="Iluminação LED",
        potencia_kw=Decimal("0.1"),
        qtd_peq=Decimal("6"),
        qtd_med=Decimal("10"),
        qtd_grande=Decimal("20"),
        perfil_horario=PERFIL_OK,
    )
    assert e.area is Area.ESCRITORIO


def test_equipamento_perfil_tamanho_errado():
    with pytest.raises(ValidationError):
        EquipamentoCreate(
            id="X",
            area=Area.COZINHA,
            equipamento="x",
            potencia_kw=Decimal("1"),
            qtd_peq=Decimal("1"),
            qtd_med=Decimal("1"),
            qtd_grande=Decimal("1"),
            perfil_horario=[0.0] * 23,
        )


def test_equipamento_perfil_fora_de_faixa():
    with pytest.raises(ValidationError):
        EquipamentoCreate(
            id="X",
            area=Area.COZINHA,
            equipamento="x",
            potencia_kw=Decimal("1"),
            qtd_peq=Decimal("1"),
            qtd_med=Decimal("1"),
            qtd_grande=Decimal("1"),
            perfil_horario=[1.5] + [0.0] * 23,
        )


def test_geracao_eficiencia_pct_intervalo():
    ok = ConfiguracaoGeracaoCreate(
        id="SOL-PEQ",
        tipo=TipoGeracao.SOLAR_FV,
        pot_nominal_kwp=Decimal("10"),
        eficiencia_pct=Decimal("85"),
        ref_conversao=Decimal("1100"),
        gen_max_kw=Decimal("10"),
        gen_min_kw=Decimal("0.5"),
    )
    assert ok.eficiencia_pct == Decimal("85")
    with pytest.raises(ValidationError):
        ConfiguracaoGeracaoCreate(
            id="X",
            tipo=TipoGeracao.SOLAR_FV,
            pot_nominal_kwp=Decimal("10"),
            eficiencia_pct=Decimal("150"),
            ref_conversao=Decimal("1100"),
            gen_max_kw=Decimal("10"),
            gen_min_kw=Decimal("0.5"),
        )


def _horas(n=24):
    return [
        TarifaHoraCreate(
            hora=h,
            preco_kwh=Decimal("0.6813"),
            tipo=TipoHorario.PONTA if h in (18, 19, 20) else TipoHorario.FORA_PONTA,
        )
        for h in range(n)
    ]


def test_tarifa_24_horas_ok():
    t = TarifaCreate(nome="AZUL_HOROSSAZONAL", horas=_horas())
    assert len(t.horas) == 24


def test_tarifa_menos_de_24_horas_falha():
    with pytest.raises(ValidationError):
        TarifaCreate(nome="X", horas=_horas(23))


def test_tarifa_hora_duplicada_falha():
    horas = _horas()
    horas[1] = TarifaHoraCreate(hora=0, preco_kwh=Decimal("0.6813"), tipo=TipoHorario.FORA_PONTA)
    with pytest.raises(ValidationError):
        TarifaCreate(nome="X", horas=horas)
