from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.geracao import (
    ConfiguracaoGeracao,
    ConfiguracaoGeracaoCreate,
    ConfiguracaoGeracaoUpdate,
)
from fems.repositories.geracao_repository import ConfiguracaoGeracaoRepository


class ConfiguracaoGeracaoService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ConfiguracaoGeracaoRepository(session)

    async def create(self, data: ConfiguracaoGeracaoCreate) -> ConfiguracaoGeracao:
        orm = await self.repo.create(data)
        return ConfiguracaoGeracao.model_validate(orm)

    async def get_by_id(self, id_: str) -> ConfiguracaoGeracao | None:
        orm = await self.repo.get_by_id(id_)
        return ConfiguracaoGeracao.model_validate(orm) if orm else None

    async def list(self) -> list[ConfiguracaoGeracao]:
        orms = await self.repo.list()
        return [ConfiguracaoGeracao.model_validate(o) for o in orms]

    async def update(self, id_: str, data: ConfiguracaoGeracaoUpdate) -> ConfiguracaoGeracao | None:
        orm = await self.repo.update(id_, data)
        return ConfiguracaoGeracao.model_validate(orm) if orm else None

    async def delete(self, id_: str) -> bool:
        return await self.repo.delete(id_)
