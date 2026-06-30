from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.equipamento import (
    Equipamento,
    EquipamentoCreate,
    EquipamentoUpdate,
)
from fems.repositories.equipamento_repository import EquipamentoRepository


class EquipamentoService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = EquipamentoRepository(session)

    async def create(self, data: EquipamentoCreate) -> Equipamento:
        orm = await self.repo.create(data)
        return Equipamento.model_validate(orm)

    async def get_by_id(self, id_: str) -> Equipamento | None:
        orm = await self.repo.get_by_id(id_)
        return Equipamento.model_validate(orm) if orm else None

    async def list(self) -> list[Equipamento]:
        orms = await self.repo.list()
        return [Equipamento.model_validate(o) for o in orms]

    async def update(self, id_: str, data: EquipamentoUpdate) -> Equipamento | None:
        orm = await self.repo.update(id_, data)
        return Equipamento.model_validate(orm) if orm else None

    async def delete(self, id_: str) -> bool:
        return await self.repo.delete(id_)
