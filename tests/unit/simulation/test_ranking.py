"""Ranking de equipamentos por área."""

import pytest

from fems.data.catalog_seed import EQUIPAMENTOS, TARIFA_AZUL
from fems.domain.configuration.enums import Area, Porte
from fems.domain.instance.ranking import ranking_por_area
from fems.domain.instance.resolver import resolver_equipamentos


def _ranking(porte):
    return ranking_por_area(resolver_equipamentos(EQUIPAMENTOS, porte), TARIFA_AZUL)


def test_quatro_areas_presentes():
    assert set(_ranking(Porte.MEDIA)) == {
        Area.ESCRITORIO,
        Area.COZINHA,
        Area.QUARTO,
        Area.IRRIGACAO,
    }


def test_ordenado_desc_por_kwh():
    for itens in _ranking(Porte.MEDIA).values():
        kwhs = [i.kwh_ano for i in itens]
        assert kwhs == sorted(kwhs, reverse=True)


def test_pct_area_soma_100():
    for itens in _ranking(Porte.MEDIA).values():
        if any(i.kwh_ano > 0 for i in itens):
            assert sum(i.pct_area for i in itens) == pytest.approx(100.0)


def test_residenciais_surgem_no_proprio_ranking():
    # Ar-condicionado (ESC-04) lidera o Escritório mesmo com a irrigação dominando o total
    r = _ranking(Porte.MEDIA)
    assert r[Area.ESCRITORIO][0].equipamento_id == "ESC-04"


def test_irrigacao_bomba_lidera_na_media():
    r = _ranking(Porte.MEDIA)
    assert r[Area.IRRIGACAO][0].equipamento_id == "IRR-02"  # Bomba auxiliar 22 kW


def test_custo_nao_negativo():
    r = _ranking(Porte.MEDIA)
    assert all(i.custo_ano >= 0 for itens in r.values() for i in itens)
