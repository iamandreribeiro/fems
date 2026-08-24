"""Geração automática de id de equipamento (PREFIX-NN) e de fazenda (FAZ-NNN)."""

from decimal import Decimal

from fems.domain.configuration.enums import Area
from fems.domain.configuration.equipamento import EquipamentoCreate, gerar_id_equipamento
from fems.domain.instance.fazenda import FazendaCreate, gerar_id_fazenda


def test_primeiro_id_por_area():
    assert gerar_id_equipamento(Area.ESCRITORIO, []) == "ESC-01"
    assert gerar_id_equipamento(Area.COZINHA, []) == "COZ-01"
    assert gerar_id_equipamento(Area.QUARTO, []) == "QUA-01"
    assert gerar_id_equipamento(Area.IRRIGACAO, []) == "IRR-01"


def test_incrementa_maior_sufixo():
    assert gerar_id_equipamento(Area.ESCRITORIO, ["ESC-01", "ESC-02"]) == "ESC-03"
    # buracos na sequência: incrementa o MAIOR, não conta a quantidade
    assert gerar_id_equipamento(Area.ESCRITORIO, ["ESC-01", "ESC-05"]) == "ESC-06"


def test_isola_por_prefixo():
    ids = ["ESC-01", "COZ-01", "COZ-02", "IRR-09"]
    assert gerar_id_equipamento(Area.COZINHA, ids) == "COZ-03"
    assert gerar_id_equipamento(Area.ESCRITORIO, ids) == "ESC-02"


def test_ignora_sufixo_nao_numerico():
    # ids legados sujos (criados à mão via Swagger) não quebram a geração
    assert gerar_id_equipamento(Area.ESCRITORIO, ["ESC-01", "ESC-string", "string"]) == "ESC-02"


def test_create_aceita_id_omitido():
    e = EquipamentoCreate(
        area=Area.ESCRITORIO,
        equipamento="Ventilador",
        potencia_kw=Decimal("0.1"),
        qtd_peq=Decimal("1"),
        qtd_med=Decimal("1"),
        qtd_grande=Decimal("1"),
        perfil_horario=[1.0] * 24,
    )
    assert e.id is None


def test_fazenda_id_formato_3_digitos():
    assert gerar_id_fazenda([]) == "FAZ-001"
    assert gerar_id_fazenda(["FAZ-001", "FAZ-002", "FAZ-004"]) == "FAZ-005"
    # ids sujos não quebram
    assert gerar_id_fazenda(["FAZ-001", "FAZ-abc", "outro"]) == "FAZ-002"


def test_fazenda_create_aceita_id_omitido():
    f = FazendaCreate(nome="Fazenda X", tamanho_ha=Decimal("80"), tipo="Pequena")
    assert f.id is None
