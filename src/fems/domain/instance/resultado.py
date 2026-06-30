"""DTOs de saída da simulação (derivados) — fatura horária e resumo mensal.

Mapeiam 1:1 dos dataclasses puros do motor (`FaturaHora`, `ResumoMes`) via
`from_attributes`, para serialização na API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from fems.domain.configuration.enums import TipoHorario


class FaturaHoraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class ResumoMesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
