from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.geracao import (
    ConfiguracaoGeracaoCreate,
    ConfiguracaoGeracaoUpdate,
)
from fems.repositories.models import ConfiguracaoGeracaoORM


class ConfiguracaoGeracaoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: ConfiguracaoGeracaoCreate) -> ConfiguracaoGeracaoORM:
        orm = ConfiguracaoGeracaoORM(**data.model_dump())
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm)
        return orm

    async def get_by_id(self, id_: str) -> ConfiguracaoGeracaoORM | None:
        return await self.session.get(ConfiguracaoGeracaoORM, id_)

    async def list(self) -> list[ConfiguracaoGeracaoORM]:
        result = await self.session.execute(
            select(ConfiguracaoGeracaoORM).order_by(ConfiguracaoGeracaoORM.id)
        )
        return list(result.scalars().all())

    async def update(
        self, id_: str, data: ConfiguracaoGeracaoUpdate
    ) -> ConfiguracaoGeracaoORM | None:
        orm = await self.session.get(ConfiguracaoGeracaoORM, id_)
        if orm is None:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(orm, key, value)
        await self.session.flush()
        await self.session.refresh(orm)
        return orm

    async def delete(self, id_: str) -> bool:
        orm = await self.session.get(ConfiguracaoGeracaoORM, id_)
        if orm is None:
            return False
        await self.session.delete(orm)
        await self.session.flush()
        return True
