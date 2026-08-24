"""Cadastro de fazenda (instância) — modelos Pydantic da API/CLI.

`FazendaCreate` é o payload de `POST /fazendas` e o formato do arquivo de config da
CLI. `FazendaRead` devolve o cadastro persistido + as cargas instanciadas derivadas.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from fems.domain.configuration.enums import Porte, StatusCarga, TipoCarga
from fems.domain.instance.override import OverrideEquipamento, OverrideEquipamentoCreate

TARIFA_PADRAO = "AZUL_HOROSSAZONAL"


class FazendaBase(BaseModel):
    id: str = Field(min_length=1, max_length=20)  # FAZ-001
    nome: str = Field(min_length=1, max_length=150)
    tamanho_ha: Decimal = Field(gt=Decimal("0"), max_digits=10, decimal_places=2)
    tipo: Porte
    tem_escritorio: bool = True
    tem_cozinha: bool = True
    tem_quarto: bool = True
    tem_irrigacao: bool = True
    id_solar: str | None = Field(default=None, max_length=20)
    id_eolica: str | None = Field(default=None, max_length=20)
    id_bateria: str | None = Field(default=None, max_length=20)
    tarifa: str = Field(default=TARIFA_PADRAO, min_length=1, max_length=100)
    seed: int = Field(default=20250101, ge=0)
    ano: int = Field(default=2025, ge=1970, le=9999)


class FazendaCreate(FazendaBase):
    # id opcional: quando omitido, o service gera no formato FAZ-NNN.
    id: str | None = Field(default=None, max_length=20)  # type: ignore[assignment]
    overrides: list[OverrideEquipamentoCreate] = Field(default_factory=list)


def gerar_id_fazenda(ids_existentes: list[str]) -> str:
    """Gera o próximo id de fazenda no formato `FAZ-NNN` (FAZ-001, FAZ-002, ...).

    Considera só o sufixo numérico dos ids `FAZ-*` já usados (ignora sufixos
    não-inteiros) e incrementa o maior. Mesmo método do id de equipamento.
    """
    marca = "FAZ-"
    numeros = [
        int(id_[len(marca) :])
        for id_ in ids_existentes
        if id_.startswith(marca) and id_[len(marca) :].isdigit()
    ]
    return f"FAZ-{max(numeros, default=0) + 1:03d}"


class FazendaCargaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carga: str
    tipo: TipoCarga
    cons_max_kw: Decimal
    cons_min_kw: Decimal
    status: StatusCarga


class FazendaRead(FazendaBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
    cargas: list[FazendaCargaRead] = Field(default_factory=list)
    overrides: list[OverrideEquipamento] = Field(default_factory=list)
