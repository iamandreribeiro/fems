from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.repositories.models import FazendaCargaORM, FazendaORM


class FazendaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, orm: FazendaORM, cargas: list[FazendaCargaORM]) -> FazendaORM:
        orm.cargas = cargas
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm, ["cargas"])
        return orm

    async def get_by_id(self, id_: str) -> FazendaORM | None:
        return await self.session.get(FazendaORM, id_)

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
