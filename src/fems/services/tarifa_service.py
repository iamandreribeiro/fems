from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.tarifa import Tarifa, TarifaCreate, TarifaUpdate
from fems.repositories.tarifa_repository import TarifaRepository


class TarifaService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TarifaRepository(session)

    async def create(self, data: TarifaCreate) -> Tarifa:
        orm = await self.repo.create(data)
        return Tarifa.model_validate(orm)

    async def get_by_id(self, id_: int) -> Tarifa | None:
        orm = await self.repo.get_by_id(id_)
        return Tarifa.model_validate(orm) if orm else None

    async def list(self) -> list[Tarifa]:
        orms = await self.repo.list()
        return [Tarifa.model_validate(o) for o in orms]

    async def update(self, id_: int, data: TarifaUpdate) -> Tarifa | None:
        orm = await self.repo.update(id_, data)
        return Tarifa.model_validate(orm) if orm else None

    async def delete(self, id_: int) -> bool:
        return await self.repo.delete(id_)
