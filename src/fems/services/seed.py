"""Seeding do catálogo de configuração a partir de `fems.data.catalog_seed`.

Reutilizável pelo script `scripts/seed_catalog.py` e pelos testes de integração.
Idempotente: upsert por chave (equipamentos/geração por id; tarifa por nome).
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL, TARIFA_AZUL_NOME
from fems.repositories.models import (
    ConfiguracaoGeracaoORM,
    EquipamentoORM,
    TarifaHoraORM,
    TarifaORM,
)


def _d(x: float) -> Decimal:
    return Decimal(str(x))


async def seed_catalogo(session: AsyncSession) -> None:
    for e in EQUIPAMENTOS:
        await session.merge(
            EquipamentoORM(
                id=e.id,
                area=e.area,
                equipamento=e.equipamento,
                potencia_kw=_d(e.potencia_kw),
                qtd_peq=_d(e.qtd_peq),
                qtd_med=_d(e.qtd_med),
                perfil_horario=list(e.perfil),
            )
        )
    for g in GERADORES:
        await session.merge(
            ConfiguracaoGeracaoORM(
                id=g.id,
                tipo=g.tipo,
                pot_nominal_kwp=_d(g.pot_nominal_kwp),
                eficiencia_pct=_d(g.eficiencia_pct),
                ref_conversao=_d(g.ref_conversao),
                gen_max_kw=_d(g.gen_max_kw),
                gen_min_kw=_d(g.gen_min_kw),
            )
        )

    existing = (
        (await session.execute(select(TarifaORM).where(TarifaORM.nome == TARIFA_AZUL_NOME)))
        .scalars()
        .first()
    )
    if existing is not None:
        await session.execute(delete(TarifaORM).where(TarifaORM.nome == TARIFA_AZUL_NOME))
        await session.flush()
    tarifa = TarifaORM(nome=TARIFA_AZUL_NOME, moeda="BRL")
    tarifa.horas = [
        TarifaHoraORM(hora=h.hora, preco_kwh=_d(h.preco_kwh), tipo=h.tipo) for h in TARIFA_AZUL
    ]
    session.add(tarifa)
