"""Popula o catálogo + as fazendas de referência a partir de `fems.data`.

Idempotente (catálogo por chave; fazendas pulam as já existentes). Use após
`alembic upgrade head`.

Run:  uv run python scripts/seed_catalog.py
      (ou: .venv/Scripts/python scripts/seed_catalog.py)
"""

from __future__ import annotations

import asyncio

from fems.core.database import SessionLocal
from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL, TARIFA_AZUL_NOME
from fems.data.fazendas_seed import FAZENDAS_REFERENCIA
from fems.services.seed import seed_catalogo, seed_fazendas


async def main() -> None:
    async with SessionLocal() as session:
        await seed_catalogo(session)
        criadas = await seed_fazendas(session)
        await session.commit()
    print(
        f"seed OK: {len(EQUIPAMENTOS)} equipamentos, {len(GERADORES)} geradores, "
        f"tarifa '{TARIFA_AZUL_NOME}' ({len(TARIFA_AZUL)} horas)"
    )
    puladas = len(FAZENDAS_REFERENCIA) - criadas
    print(f"fazendas de referência: {criadas} criada(s), {puladas} já existia(m)")


if __name__ == "__main__":
    asyncio.run(main())
