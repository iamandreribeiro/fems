"""Cadastro personalizado — override parcial de equipamentos por fazenda.

Campos nulos = manter o valor do catálogo para o porte. Usado no payload de
`POST /fazendas` (`overrides`) e ecoado em `FazendaRead`.
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fems.domain.configuration.equipamento import HOURS_IN_DAY, validate_perfil


class OverrideEquipamentoBase(BaseModel):
    equipamento_id: str = Field(min_length=1, max_length=20)
    qtd: Decimal | None = Field(default=None, ge=Decimal("0"), max_digits=6, decimal_places=2)
    potencia_kw: Decimal | None = Field(
        default=None, gt=Decimal("0"), max_digits=10, decimal_places=4
    )
    perfil_horario: list[float] | None = Field(
        default=None, min_length=HOURS_IN_DAY, max_length=HOURS_IN_DAY
    )

    @field_validator("perfil_horario")
    @classmethod
    def _perfil_ok(cls, v: list[float] | None) -> list[float] | None:
        return None if v is None else validate_perfil(v)


class OverrideEquipamentoCreate(OverrideEquipamentoBase):
    pass


class OverrideEquipamento(OverrideEquipamentoBase):
    model_config = ConfigDict(from_attributes=True)
