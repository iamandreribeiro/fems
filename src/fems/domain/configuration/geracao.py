"""Configuração de geração — espelha a aba `Config_Geracao` da planilha v8.

Geração (solar e eólica) é computada a partir do clima (GHI / vento), normalizada
pela referência de conversão, vezes potência e eficiência, com clamp min/max — e
**não** por uma curva horária estática. Por isso os parâmetros abaixo são colunas
tipadas de primeira classe (não um blob JSON).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from fems.domain.configuration.enums import TipoGeracao


class ConfiguracaoGeracaoBase(BaseModel):
    id: str = Field(min_length=1, max_length=20)  # SOL-PEQ, EOL-MED...
    tipo: TipoGeracao
    pot_nominal_kwp: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=4)
    eficiencia_pct: Decimal = Field(
        gt=Decimal("0"), le=Decimal("100"), max_digits=5, decimal_places=2
    )
    ref_conversao: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=4)
    gen_max_kw: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=4)
    gen_min_kw: Decimal = Field(ge=Decimal("0"), max_digits=10, decimal_places=4)


class ConfiguracaoGeracaoCreate(ConfiguracaoGeracaoBase):
    pass


class ConfiguracaoGeracaoUpdate(BaseModel):
    tipo: TipoGeracao | None = None
    pot_nominal_kwp: Decimal | None = Field(
        default=None, gt=Decimal("0"), max_digits=10, decimal_places=4
    )
    eficiencia_pct: Decimal | None = Field(
        default=None, gt=Decimal("0"), le=Decimal("100"), max_digits=5, decimal_places=2
    )
    ref_conversao: Decimal | None = Field(
        default=None, gt=Decimal("0"), max_digits=10, decimal_places=4
    )
    gen_max_kw: Decimal | None = Field(
        default=None, gt=Decimal("0"), max_digits=10, decimal_places=4
    )
    gen_min_kw: Decimal | None = Field(
        default=None, ge=Decimal("0"), max_digits=10, decimal_places=4
    )


class ConfiguracaoGeracao(ConfiguracaoGeracaoBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
