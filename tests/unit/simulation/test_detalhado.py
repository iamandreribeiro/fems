"""Modo detalhado do motor: abas por-carga e por-gerador, consistentes com a fatura."""

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL
from fems.data.clima import carregar_clima
from fems.domain.configuration.enums import Porte
from fems.domain.simulation.engine import simular_fazenda
from fems.domain.simulation.types import FazendaSpec

GER = {g.id: g for g in GERADORES}
CLIMA = carregar_clima(2025)

FAZ = FazendaSpec(
    id="FAZ-002",
    nome="São Pedro",
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
)


def test_sem_detalhado_nao_gera_series():
    r = simular_fazenda(FAZ, EQUIPAMENTOS, GER, TARIFA_AZUL, CLIMA)
    assert r.cargas_horarias == []
    assert r.geracao_horaria == []
    assert len(r.equipamentos) == len(EQUIPAMENTOS)  # sempre populado


def test_detalhado_tamanhos():
    r = simular_fazenda(FAZ, EQUIPAMENTOS, GER, TARIFA_AZUL, CLIMA, detalhado=True)
    assert len(r.cargas_horarias) == 7 * 8760  # 7 cargas (sem bateria) x horas
    assert len(r.geracao_horaria) == 2 * 8760  # solar + eolica x horas


def test_detalhado_consistente_com_fatura():
    r = simular_fazenda(FAZ, EQUIPAMENTOS, GER, TARIFA_AZUL, CLIMA, detalhado=True)
    # soma das cargas por hora == consumo da fatura; idem geração
    consumo_por_hora: dict[int, float] = {}
    for c in r.cargas_horarias:
        consumo_por_hora[c.data_hora.toordinal() * 24 + c.hora] = (
            consumo_por_hora.get(c.data_hora.toordinal() * 24 + c.hora, 0.0) + c.consumo_kwh
        )
    ger_por_hora: dict[int, float] = {}
    for g in r.geracao_horaria:
        ger_por_hora[g.data_hora.toordinal() * 24 + g.hora] = (
            ger_por_hora.get(g.data_hora.toordinal() * 24 + g.hora, 0.0) + g.energia_kwh
        )
    for f in r.fatura:
        chave = f.data_hora.toordinal() * 24 + f.hora
        assert abs(consumo_por_hora.get(chave, 0.0) - f.consumo_kwh) < 1e-9
        assert abs(ger_por_hora.get(chave, 0.0) - f.geracao_kwh) < 1e-9
