"""Porte Grande: cargas maiores que a Média, geração GRD clampa, catálogo tem GRD."""

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES
from fems.domain.configuration.enums import Porte
from fems.domain.instance.instanciar import instanciar_cargas
from fems.domain.simulation.geracao import gerar_solar
from fems.domain.simulation.types import FazendaSpec

GER = {g.id: g for g in GERADORES}


def _faz(porte, id_solar):
    return FazendaSpec(
        id="F",
        nome="x",
        tamanho_ha=1500.0,
        porte=porte,
        tem_escritorio=True,
        tem_cozinha=True,
        tem_quarto=True,
        tem_irrigacao=True,
        id_solar=id_solar,
        id_eolica="EOL-GRD",
        id_bateria="BAT-001",
        tarifa="AZUL_HOROSSAZONAL",
        seed=1,
        ano=2025,
    )


def test_catalogo_tem_geracao_grande():
    assert "SOL-GRD" in GER
    assert "EOL-GRD" in GER


def test_grande_cargas_maiores_que_media():
    med = {c.carga: c for c in instanciar_cargas(_faz(Porte.MEDIA, "SOL-MED"), EQUIPAMENTOS)}
    grd = {c.carga: c for c in instanciar_cargas(_faz(Porte.GRANDE, "SOL-GRD"), EQUIPAMENTOS)}
    assert grd["Escritório"].cons_max_kw > med["Escritório"].cons_max_kw
    assert grd["Bateria"].cons_max_kw >= med["Bateria"].cons_max_kw


def test_sol_grd_clampa_no_gen_max():
    assert gerar_solar(5000.0, 1.0, GER["SOL-GRD"]) == GER["SOL-GRD"].gen_max_kw == 100.0
