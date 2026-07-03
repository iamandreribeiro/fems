"""Perfil_Area — agregação paramétrica de potência por (carga, porte, hora).

Espelha a aba `Perfil_Area`: cada célula é um SUMPRODUCT sobre `Config_Equipamentos`
(filtro de área * potência * quantidade do porte * fator horário). As cargas
agrícolas adicionam um segundo filtro pelo nome do equipamento.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fems.domain.configuration.enums import Area, TipoCarga
from fems.domain.simulation.types import HOURS_IN_DAY, EquipamentoResolvido


@dataclass(frozen=True, slots=True)
class LoadDef:
    """Definição de uma carga agregada e como derivá-la do catálogo."""

    carga: str
    area: Area
    equipamento: str | None  # filtro adicional por nome (cargas agrícolas); None = toda a área
    tipo: TipoCarga
    flag: str  # atributo de FazendaSpec que ativa/inativa esta carga


# Ordem espelha o Cadastro_Cargas da planilha (7 cargas; bateria é anexada à parte).
_AGRI = TipoCarga.AGRICOLA
_SEDE = TipoCarga.SEDE
_IRR = "tem_irrigacao"
LOAD_DEFS: tuple[LoadDef, ...] = (
    LoadDef("Pivô", Area.IRRIGACAO, "Pivô central", _AGRI, _IRR),
    LoadDef("Bomba_Aux", Area.IRRIGACAO, "Bomba auxiliar", _AGRI, _IRR),
    LoadDef("Secadora", Area.IRRIGACAO, "Secadora/Silo", _AGRI, _IRR),
    LoadDef("Quadro_Auto", Area.IRRIGACAO, "Quadro de automação", _AGRI, _IRR),
    LoadDef("Escritório", Area.ESCRITORIO, None, _SEDE, "tem_escritorio"),
    LoadDef("Cozinha", Area.COZINHA, None, _SEDE, "tem_cozinha"),
    LoadDef("Quarto", Area.QUARTO, None, _SEDE, "tem_quarto"),
)


def perfil_area_24h(
    equipamentos: Sequence[EquipamentoResolvido], load: LoadDef
) -> tuple[float, ...]:
    """Potência (kW) por hora para uma carga — 24 valores. `equipamentos` já resolvidos."""
    selecionados = [
        e
        for e in equipamentos
        if e.area == load.area and (load.equipamento is None or e.equipamento == load.equipamento)
    ]
    out: list[float] = []
    for h in range(HOURS_IN_DAY):
        total = 0.0
        for e in selecionados:
            total += e.potencia_kw * e.qtd * e.perfil[h]
        out.append(total)
    return tuple(out)


def perfis_por_carga(
    equipamentos: Sequence[EquipamentoResolvido],
) -> list[tuple[LoadDef, tuple[float, ...]]]:
    """Perfil de 24h para cada carga definida."""
    return [(ld, perfil_area_24h(equipamentos, ld)) for ld in LOAD_DEFS]
