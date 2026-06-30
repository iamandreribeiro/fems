"""Tarifa horossazonal — espelha a aba `Tarifa` da planilha v8 (24 linhas horárias).

Cada hora tem um preço e um tipo (Ponta / Fora Ponta). O tipo é essencial: define
as horas de descarga da bateria e o split de custo Ponta vs Fora-Ponta no resumo.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fems.domain.configuration.enums import TipoHorario

HOURS_IN_DAY = 24


class TarifaHoraBase(BaseModel):
    hora: int = Field(ge=0, le=23)
    preco_kwh: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=6)
    tipo: TipoHorario


class TarifaHoraCreate(TarifaHoraBase):
    pass


class TarifaHora(TarifaHoraBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarifa_id: int


class TarifaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    moeda: str = Field(default="BRL", min_length=3, max_length=3)


class TarifaCreate(TarifaBase):
    horas: list[TarifaHoraCreate] = Field(min_length=HOURS_IN_DAY, max_length=HOURS_IN_DAY)

    @field_validator("horas")
    @classmethod
    def _horas_completas(cls, v: list[TarifaHoraCreate]) -> list[TarifaHoraCreate]:
        if {h.hora for h in v} != set(range(HOURS_IN_DAY)):
            raise ValueError("horas devem cobrir exatamente 0..23 sem repetição")
        return v


class TarifaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    moeda: str | None = Field(default=None, min_length=3, max_length=3)
    horas: list[TarifaHoraCreate] | None = Field(
        default=None, min_length=HOURS_IN_DAY, max_length=HOURS_IN_DAY
    )


class Tarifa(TarifaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    horas: list[TarifaHora] = Field(default_factory=list)
