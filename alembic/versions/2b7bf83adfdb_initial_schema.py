"""initial schema

Revision ID: 2b7bf83adfdb
Revises:
Create Date: 2026-06-05 14:06:45.466768

Reescrita na refatoração FEMS: catálogo reconciliado com a planilha v8
(config_equipamento com qtd_peq/qtd_med + perfil inline; geração com parâmetros
tipados; tarifa horária com tipo Ponta/Fora-Ponta) + camada de cadastro
(fazenda + fazenda_cargas). DB de desenvolvimento/vazio: migração única,
não corretiva.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "2b7bf83adfdb"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "config_equipamento",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column(
            "area",
            postgresql.ENUM("escritorio", "cozinha", "quarto", "irrigacao", name="area_enum"),
            nullable=False,
        ),
        sa.Column("equipamento", sa.String(length=100), nullable=False),
        sa.Column("potencia_kw", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("qtd_peq", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("qtd_med", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("perfil_horario", sa.ARRAY(sa.Float()), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "configuracoes_geracao",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM("solar_fv", "eolica", name="tipo_geracao_enum"),
            nullable=False,
        ),
        sa.Column("pot_nominal_kwp", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("eficiencia_pct", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("ref_conversao", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("gen_max_kw", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("gen_min_kw", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tarifas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("moeda", sa.String(length=3), server_default="BRL", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_table(
        "tarifa_horas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tarifa_id", sa.Integer(), nullable=False),
        sa.Column("hora", sa.SmallInteger(), nullable=False),
        sa.Column("preco_kwh", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM("Ponta", "Fora Ponta", name="tipo_horario_enum"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tarifa_id"], ["tarifas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fazenda",
        sa.Column("id", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("tamanho_ha", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM("Pequena", "Média", name="porte_enum"),
            nullable=False,
        ),
        sa.Column("tem_escritorio", sa.Boolean(), nullable=False),
        sa.Column("tem_cozinha", sa.Boolean(), nullable=False),
        sa.Column("tem_quarto", sa.Boolean(), nullable=False),
        sa.Column("tem_irrigacao", sa.Boolean(), nullable=False),
        sa.Column("id_solar", sa.String(length=20), nullable=True),
        sa.Column("id_eolica", sa.String(length=20), nullable=True),
        sa.Column("id_bateria", sa.String(length=20), nullable=True),
        sa.Column("tarifa", sa.String(length=100), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("ano", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_solar"], ["configuracoes_geracao.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["id_eolica"], ["configuracoes_geracao.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fazenda_cargas",
        sa.Column("fazenda_id", sa.String(length=20), nullable=False),
        sa.Column("carga", sa.String(length=50), nullable=False),
        sa.Column(
            "tipo",
            postgresql.ENUM("Agrícola", "Sede", "Armazenamento", name="tipo_carga_enum"),
            nullable=False,
        ),
        sa.Column("cons_max_kw", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column("cons_min_kw", sa.Numeric(precision=12, scale=6), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("Ativo", "Inativo", name="status_carga_enum"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("fazenda_id", "carga"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("fazenda_cargas")
    op.drop_table("fazenda")
    op.drop_table("tarifa_horas")
    op.drop_table("tarifas")
    op.drop_table("configuracoes_geracao")
    op.drop_table("config_equipamento")
    # PG ENUM types persist after table drops; drop them explicitly
    for enum_name in (
        "area_enum",
        "tipo_geracao_enum",
        "tipo_horario_enum",
        "porte_enum",
        "tipo_carga_enum",
        "status_carga_enum",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
