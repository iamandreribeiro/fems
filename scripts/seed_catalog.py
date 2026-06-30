"""Popula as tabelas de configuração (catálogo) a partir de `fems.data.catalog_seed`.

Idempotente (upsert por chave). Use após `alembic upgrade head`.

Run:  uv run python scripts/seed_catalog.py
      (ou: .venv/Scripts/python scripts/seed_catalog.py)
"""

from __future__ import annotations

import asyncio

from fems.core.database import SessionLocal
from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL, TARIFA_AZUL_NOME
from fems.services.seed import seed_catalogo


async def main() -> None:
    async with SessionLocal() as session:
        await seed_catalogo(session)
        await session.commit()
    print(
        f"seed OK: {len(EQUIPAMENTOS)} equipamentos, {len(GERADORES)} geradores, "
        f"tarifa '{TARIFA_AZUL_NOME}' ({len(TARIFA_AZUL)} horas)"
    )


if __name__ == "__main__":
    asyncio.run(main())
