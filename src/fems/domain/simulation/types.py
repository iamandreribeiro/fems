"""Tipos puros do motor de simulação (dataclasses frozen, sem I/O).

São o vocabulário do domínio rico: entram catálogo + clima + fazenda; saem fatura
horária + resumo mensal. A API/BD usam os modelos Pydantic/ORM e convertem para
estes tipos na fronteira do service (ver `fems.services.fazenda_service`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fems.domain.configuration.enums import (
    Area,
    Porte,
    StatusCarga,
    TipoCarga,
    TipoGeracao,
    TipoHorario,
)

HOURS_IN_DAY = 24


@dataclass(frozen=True, slots=True)
class Equipamento:
    """Equipamento de catálogo (Config_Equipamentos) com perfil horário inline."""

    id: str
    area: Area
    equipamento: str
    potencia_kw: float
    qtd_peq: float
    qtd_med: float
    perfil: tuple[float, ...]  # 24 fatores 0..1


@dataclass(frozen=True, slots=True)
class Gerador:
    """Configuração de um gerador (Config_Geracao)."""

    id: str
    tipo: TipoGeracao
    pot_nominal_kwp: float
    eficiencia_pct: float
    ref_conversao: float
    gen_max_kw: float
    gen_min_kw: float


@dataclass(frozen=True, slots=True)
class TarifaHora:
    """Preço e classificação de uma hora (Tarifa)."""

    hora: int
    preco_kwh: float
    tipo: TipoHorario


@dataclass(frozen=True, slots=True)
class ClimaHora:
    """Uma hora da base climática (Base_Irradiacao)."""

    indice: int  # 0..8759 (hora absoluta no ano)
    data_hora: datetime
    mes: int
    hora: int
    ghi: float
    temp: float
    vento: float
    fp: float


@dataclass(frozen=True, slots=True)
class FazendaSpec:
    """Estado paramétrico de uma fazenda — entrada do motor (Cadastro_Fazenda)."""

    id: str
    nome: str
    tamanho_ha: float
    porte: Porte
    tem_escritorio: bool
    tem_cozinha: bool
    tem_quarto: bool
    tem_irrigacao: bool
    id_solar: str | None
    id_eolica: str | None
    id_bateria: str | None
    tarifa: str
    seed: int
    ano: int


@dataclass(frozen=True, slots=True)
class CargaInstanciada:
    """Carga derivada para uma fazenda (Cadastro_Cargas)."""

    carga: str
    tipo: TipoCarga
    cons_max_kw: float
    cons_min_kw: float
    status: StatusCarga


@dataclass(frozen=True, slots=True)
class FaturaHora:
    """Uma linha horária de fatura (Consumo_Fatura)."""

    id_fazenda: str
    data_hora: datetime
    mes: int
    hora: int
    consumo_kwh: float
    geracao_kwh: float
    saldo_rede_kwh: float
    tarifa_rs: float
    custo_rs: float
    tipo_horario: TipoHorario
    bateria_descarga_kwh: float
    saldo_liquido_kwh: float


@dataclass(frozen=True, slots=True)
class ResumoMes:
    """Agregação mensal por fazenda (Resumo_Mensal)."""

    id_fazenda: str
    mes: int
    consumo_kwh: float
    geracao_kwh: float
    saldo_rede_kwh: float
    custo_total_rs: float
    custo_ponta_rs: float
    custo_fora_ponta_rs: float
    bateria_descarga_kwh: float
    saldo_liquido_kwh: float


@dataclass(frozen=True, slots=True)
class SimResult:
    """Resultado completo de uma simulação."""

    fazenda_id: str
    cargas: list[CargaInstanciada]
    fatura: list[FaturaHora]
    resumo: list[ResumoMes]
