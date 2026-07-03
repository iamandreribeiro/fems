"""Resolução de equipamentos: porte (peq/med/grande) + override parcial."""

from fems.data.catalog_seed import EQUIPAMENTOS
from fems.domain.configuration.enums import Porte
from fems.domain.instance.instanciar import instanciar_cargas
from fems.domain.instance.resolver import resolver_equipamentos
from fems.domain.simulation.types import FazendaSpec, OverrideSpec

CAT = {e.id: e for e in EQUIPAMENTOS}


def _by_id(resolvidos):
    return {e.id: e for e in resolvidos}


def _faz(porte):
    return FazendaSpec(
        id="F",
        nome="x",
        tamanho_ha=100.0,
        porte=porte,
        tem_escritorio=True,
        tem_cozinha=True,
        tem_quarto=True,
        tem_irrigacao=True,
        id_solar=None,
        id_eolica=None,
        id_bateria="BAT-001",
        tarifa="AZUL_HOROSSAZONAL",
        seed=1,
        ano=2025,
    )


def test_qtd_segue_o_porte():
    peq = _by_id(resolver_equipamentos(EQUIPAMENTOS, Porte.PEQUENA))
    med = _by_id(resolver_equipamentos(EQUIPAMENTOS, Porte.MEDIA))
    grd = _by_id(resolver_equipamentos(EQUIPAMENTOS, Porte.GRANDE))
    assert peq["ESC-01"].qtd == CAT["ESC-01"].qtd_peq
    assert med["ESC-01"].qtd == CAT["ESC-01"].qtd_med
    assert grd["ESC-01"].qtd == CAT["ESC-01"].qtd_grande


def test_override_substitui_apenas_campos_informados():
    ov = [OverrideSpec(equipamento_id="ESC-04", qtd=5.0, potencia_kw=1.5)]
    r = _by_id(resolver_equipamentos(EQUIPAMENTOS, Porte.MEDIA, ov))
    assert r["ESC-04"].qtd == 5.0
    assert r["ESC-04"].potencia_kw == 1.5
    assert r["ESC-04"].perfil == CAT["ESC-04"].perfil  # perfil não informado → catálogo


def test_override_perfil_mantendo_qtd_do_porte():
    novo = tuple([1.0] * 24)
    r = _by_id(
        resolver_equipamentos(EQUIPAMENTOS, Porte.PEQUENA, [OverrideSpec("COZ-03", perfil=novo)])
    )
    assert r["COZ-03"].perfil == novo
    assert r["COZ-03"].qtd == CAT["COZ-03"].qtd_peq


def test_equipamento_sem_override_inalterado():
    r = _by_id(resolver_equipamentos(EQUIPAMENTOS, Porte.MEDIA, [OverrideSpec("ESC-04", qtd=5.0)]))
    assert r["COZ-01"].qtd == CAT["COZ-01"].qtd_med
    assert r["COZ-01"].potencia_kw == CAT["COZ-01"].potencia_kw


def test_override_propaga_para_instanciacao():
    faz = _faz(Porte.MEDIA)
    base = {c.carga: c for c in instanciar_cargas(faz, EQUIPAMENTOS)}
    custom = {
        c.carga: c
        for c in instanciar_cargas(faz, EQUIPAMENTOS, [OverrideSpec("ESC-04", potencia_kw=10.0)])
    }
    # ESC-04 (ar-condicionado) entra no Escritório à hora 11 → Cons_Max sobe
    assert custom["Escritório"].cons_max_kw > base["Escritório"].cons_max_kw
