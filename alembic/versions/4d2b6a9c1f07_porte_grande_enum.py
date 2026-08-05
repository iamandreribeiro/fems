"""adiciona 'Grande' ao enum porte_enum

Revision ID: 4d2b6a9c1f07
Revises: 3c1a2f5e8b94
Create Date: 2026-06-30 12:00:00.000000

A migração 3c1a2f5e8b94 adicionou a coluna qtd_grande e a tabela fazenda_override,
mas não incluiu o valor 'Grande' no enum PostgreSQL `porte_enum` (criado só com
Pequena/Média). Sem isso, criar uma fazenda de porte Grande falha com
InvalidTextRepresentationError. `ADD VALUE` roda fora da transação (autocommit_block).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "4d2b6a9c1f07"
down_revision: str | Sequence[str] | None = "3c1a2f5e8b94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE porte_enum ADD VALUE IF NOT EXISTS 'Grande'")


def downgrade() -> None:
    # PostgreSQL não suporta remover um valor de enum; no-op (deixa 'Grande' no tipo).
    pass
