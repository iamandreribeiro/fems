"""porte grande + cadastro override

Revision ID: 3c1a2f5e8b94
Revises: 2b7bf83adfdb
Create Date: 2026-06-30 10:00:00.000000

Aditiva: adiciona config_equipamento.qtd_grande (porte Grande) e a tabela
fazenda_override (cadastro personalizado parcial por equipamento).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3c1a2f5e8b94"
down_revision: str | Sequence[str] | None = "2b7bf83adfdb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # qtd_grande: server_default temporário p/ linhas existentes; o seed reescreve.
    op.add_column(
        "config_equipamento",
        sa.Column("qtd_grande", sa.Numeric(6, 2), nullable=False, server_default="0"),
    )
    op.alter_column("config_equipamento", "qtd_grande", server_default=None)

    op.create_table(
        "fazenda_override",
        sa.Column("fazenda_id", sa.String(length=20), nullable=False),
        sa.Column("equipamento_id", sa.String(length=20), nullable=False),
        sa.Column("qtd", sa.Numeric(6, 2), nullable=True),
        sa.Column("potencia_kw", sa.Numeric(10, 4), nullable=True),
        sa.Column("perfil_horario", sa.ARRAY(sa.Float()), nullable=True),
        sa.ForeignKeyConstraint(["fazenda_id"], ["fazenda.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["equipamento_id"], ["config_equipamento.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("fazenda_id", "equipamento_id"),
    )


def downgrade() -> None:
    op.drop_table("fazenda_override")
    op.drop_column("config_equipamento", "qtd_grande")
