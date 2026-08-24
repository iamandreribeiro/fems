from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.repositories.models import FazendaCargaORM, FazendaORM, FazendaOverrideORM


class FazendaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        orm: FazendaORM,
        cargas: list[FazendaCargaORM],
        overrides: list[FazendaOverrideORM] | None = None,
    ) -> FazendaORM:
        orm.cargas = cargas
        orm.overrides = overrides or []
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm, ["cargas", "overrides"])
        return orm

    async def get_by_id(self, id_: str) -> FazendaORM | None:
        return await self.session.get(FazendaORM, id_)

    # Antes de `list` de propósito: o método `list` sombrearia o builtin `list`
    # nas anotações seguintes (list[str]) e quebraria a checagem de tipos.
    async def ids(self) -> list[str]:
        result = await self.session.execute(select(FazendaORM.id))
        return list(result.scalars().all())

    async def list(self) -> list[FazendaORM]:
        result = await self.session.execute(select(FazendaORM).order_by(FazendaORM.id))
        return list(result.scalars().all())

    async def delete(self, id_: str) -> bool:
        orm = await self.session.get(FazendaORM, id_)
        if orm is None:
            return False
        await self.session.delete(orm)
        await self.session.flush()
        return True
