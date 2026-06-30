"""Catálogo de equipamentos padrão — espelha a aba `Config_Equipamentos` da planilha v8.

Cada equipamento carrega seu perfil horario (24 fatores de 0 a 1) inline, exatamente
como na planilha. As quantidades por porte (`qtd_peq`/`qtd_med`) alimentam a agregacao
parametrica `Perfil_Area` no motor de simulacao.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fems.domain.configuration.enums import Area

HOURS_IN_DAY = 24


def validate_perfil(values: list[float]) -> list[float]:
    if len(values) != HOURS_IN_DAY:
        raise ValueError(f"perfil_horario deve ter exatamente {HOURS_IN_DAY} valores")
    if not all(0.0 <= x <= 1.0 for x in values):
        raise ValueError("todos os fatores horários devem estar em [0.0, 1.0]")
    return values


class EquipamentoBase(BaseModel):
    id: str = Field(min_length=1, max_length=20)  # ESC-01, IRR-01...
    area: Area
    equipamento: str = Field(min_length=1, max_length=100)
    potencia_kw: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=4)
    qtd_peq: Decimal = Field(ge=Decimal("0"), max_digits=6, decimal_places=2)
    qtd_med: Decimal = Field(ge=Decimal("0"), max_digits=6, decimal_places=2)
    perfil_horario: list[float] = Field(min_length=HOURS_IN_DAY, max_length=HOURS_IN_DAY)

    @field_validator("perfil_horario")
    @classmethod
    def _perfil_ok(cls, v: list[float]) -> list[float]:
        return validate_perfil(v)


class EquipamentoCreate(EquipamentoBase):
    pass


class EquipamentoUpdate(BaseModel):
    area: Area | None = None
    equipamento: str | None = Field(default=None, min_length=1, max_length=100)
    potencia_kw: Decimal | None = Field(
        default=None, gt=Decimal("0"), max_digits=10, decimal_places=4
    )
    qtd_peq: Decimal | None = Field(default=None, ge=Decimal("0"), max_digits=6, decimal_places=2)
    qtd_med: Decimal | None = Field(default=None, ge=Decimal("0"), max_digits=6, decimal_places=2)
    perfil_horario: list[float] | None = Field(
        default=None, min_length=HOURS_IN_DAY, max_length=HOURS_IN_DAY
    )

    @field_validator("perfil_horario")
    @classmethod
    def _perfil_ok(cls, v: list[float] | None) -> list[float] | None:
        return None if v is None else validate_perfil(v)


class Equipamento(EquipamentoBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
