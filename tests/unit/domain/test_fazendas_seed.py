"""Sanidade das fazendas de referência semeadas numa base nova."""

from decimal import Decimal

from fems.data.fazendas_seed import FAZENDAS_REFERENCIA
from fems.domain.configuration.enums import Porte


def test_duas_fazendas_de_referencia():
    ids = [f.id for f in FAZENDAS_REFERENCIA]
    assert ids == ["FAZ-001", "FAZ-002"]


def test_params_boa_vista_e_sao_pedro():
    boa_vista, sao_pedro = FAZENDAS_REFERENCIA
    assert (boa_vista.nome, boa_vista.tipo, boa_vista.tamanho_ha) == (
        "Fazenda Boa Vista",
        Porte.PEQUENA,
        Decimal("80"),
    )
    assert (sao_pedro.nome, sao_pedro.tipo, sao_pedro.tamanho_ha) == (
        "Fazenda São Pedro",
        Porte.MEDIA,
        Decimal("320"),
    )
