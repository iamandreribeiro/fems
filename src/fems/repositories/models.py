"""SQLAlchemy ORM — espelha as camadas da planilha v8.

Configuração (catálogo, administrável):  config_equipamento, configuracoes_geracao,
    tarifas (+ tarifa_horas).
Cadastro (instância persistida):           fazenda (+ fazenda_cargas derivadas).

A série de simulação NÃO é persistida no caminho padrão (recompute on-demand, AD-1).
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Float,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fems.core.database import Base
from fems.domain.configuration.enums import (
    Area,
    Porte,
    StatusCarga,
    TipoCarga,
    TipoGeracao,
    TipoHorario,
)


def _pg_enum(enum_cls: type[StrEnum], name: str) -> ENUM:
    return ENUM(
        enum_cls,
        name=name,
        values_callable=lambda cls: [e.value for e in cls],
        create_type=True,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


# ----------------------------------------------------------------------------- Configuração


class EquipamentoORM(TimestampMixin, Base):
    __tablename__ = "config_equipamento"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # ESC-01, IRR-01...
    area: Mapped[Area] = mapped_column(_pg_enum(Area, "area_enum"), nullable=False)
    equipamento: Mapped[str] = mapped_column(String(100), nullable=False)
    potencia_kw: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    qtd_peq: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    qtd_med: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    qtd_grande: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    perfil_horario: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)  # 24 fatores


class ConfiguracaoGeracaoORM(TimestampMixin, Base):
    __tablename__ = "configuracoes_geracao"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # SOL-PEQ, EOL-MED...
    tipo: Mapped[TipoGeracao] = mapped_column(
        _pg_enum(TipoGeracao, "tipo_geracao_enum"), nullable=False
    )
    pot_nominal_kwp: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    eficiencia_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    ref_conversao: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    gen_max_kw: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    gen_min_kw: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)


class TarifaORM(TimestampMixin, Base):
    __tablename__ = "tarifas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    moeda: Mapped[str] = mapped_column(
        String(3), nullable=False, default="BRL", server_default="BRL"
    )

    horas: Mapped[list["TarifaHoraORM"]] = relationship(
        back_populates="tarifa",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TarifaHoraORM.hora",
    )


class TarifaHoraORM(Base):
    __tablename__ = "tarifa_horas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarifa_id: Mapped[int] = mapped_column(
        ForeignKey("tarifas.id", ondelete="CASCADE"), nullable=False
    )
    hora: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    preco_kwh: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    tipo: Mapped[TipoHorario] = mapped_column(
        _pg_enum(TipoHorario, "tipo_horario_enum"), nullable=False
    )

    tarifa: Mapped[TarifaORM] = relationship(back_populates="horas")


# ----------------------------------------------------------------------------- Cadastro


class FazendaORM(TimestampMixin, Base):
    __tablename__ = "fazenda"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # FAZ-001
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    tamanho_ha: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tipo: Mapped[Porte] = mapped_column(_pg_enum(Porte, "porte_enum"), nullable=False)
    tem_escritorio: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tem_cozinha: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tem_quarto: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tem_irrigacao: Mapped[bool] = mapped_column(Boolean, nullable=False)
    id_solar: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("configuracoes_geracao.id", ondelete="RESTRICT"), nullable=True
    )
    id_eolica: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("configuracoes_geracao.id", ondelete="RESTRICT"), nullable=True
    )
    id_bateria: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tarifa: Mapped[str] = mapped_column(String(100), nullable=False, default="AZUL_HOROSSAZONAL")
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    cargas: Mapped[list["FazendaCargaORM"]] = relationship(
        back_populates="fazenda",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    overrides: Mapped[list["FazendaOverrideORM"]] = relationship(
        back_populates="fazenda",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class FazendaCargaORM(Base):
    __tablename__ = "fazenda_cargas"

    fazenda_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("fazenda.id", ondelete="CASCADE"), primary_key=True
    )
    carga: Mapped[str] = mapped_column(String(50), primary_key=True)  # Pivô, Escritório, Bateria...
    tipo: Mapped[TipoCarga] = mapped_column(_pg_enum(TipoCarga, "tipo_carga_enum"), nullable=False)
    cons_max_kw: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    cons_min_kw: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    status: Mapped[StatusCarga] = mapped_column(
        _pg_enum(StatusCarga, "status_carga_enum"), nullable=False
    )

    fazenda: Mapped[FazendaORM] = relationship(back_populates="cargas")


class FazendaOverrideORM(Base):
    """Override parcial por equipamento (cadastro personalizado). Campos nulos =
    mantém o valor do catálogo para o porte da fazenda."""

    __tablename__ = "fazenda_override"

    fazenda_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("fazenda.id", ondelete="CASCADE"), primary_key=True
    )
    equipamento_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("config_equipamento.id", ondelete="RESTRICT"), primary_key=True
    )
    qtd: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    potencia_kw: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    perfil_horario: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)

    fazenda: Mapped[FazendaORM] = relationship(back_populates="overrides")
