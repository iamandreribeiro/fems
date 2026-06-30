from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.equipamento import EquipamentoCreate, EquipamentoUpdate
from fems.repositories.models import EquipamentoORM


class EquipamentoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: EquipamentoCreate) -> EquipamentoORM:
        orm = EquipamentoORM(**data.model_dump())
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return orm

    async def get_by_id(self, id_: str) -> EquipamentoORM | None:
        return await self.session.get(EquipamentoORM, id_)

    async def list(self) -> list[EquipamentoORM]:
        result = await self.session.execute(select(EquipamentoORM).order_by(EquipamentoORM.id))
        return list(result.scalars().all())

    async def update(self, id_: str, data: EquipamentoUpdate) -> EquipamentoORM | None:
        orm = await self.session.get(EquipamentoORM, id_)
        if orm is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(orm, key, value)
        await self.session.flush()
        await self.session.refresh(orm)
        return orm

    async def delete(self, id_: str) -> bool:
        orm = await self.session.get(EquipamentoORM, id_)
        if orm is None:
            return False
        await self.session.delete(orm)
        await self.session.flush()
        return True
