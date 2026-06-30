from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fems.domain.configuration.tarifa import TarifaCreate, TarifaUpdate
from fems.repositories.models import TarifaHoraORM, TarifaORM


class TarifaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: TarifaCreate) -> TarifaORM:
        orm = TarifaORM(nome=data.nome, moeda=data.moeda)
        for hora in data.horas:
            orm.horas.append(TarifaHoraORM(**hora.model_dump()))
        self.session.add(orm)
        await self.session.flush()
        await self.session.refresh(orm, ["horas"])
        return orm

    async def get_by_id(self, id_: int) -> TarifaORM | None:
        return await self.session.get(TarifaORM, id_)

    async def get_by_nome(self, nome: str) -> TarifaORM | None:
        result = await self.session.execute(select(TarifaORM).where(TarifaORM.nome == nome))
        return result.scalars().first()

    async def list(self) -> list[TarifaORM]:
        result = await self.session.execute(select(TarifaORM).order_by(TarifaORM.id))
        return list(result.scalars().all())

    async def update(self, id_: int, data: TarifaUpdate) -> TarifaORM | None:
        orm = await self.session.get(TarifaORM, id_)
        if orm is None:
            return None
        update_data = data.model_dump(exclude_unset=True)
        horas_data = update_data.pop("horas", None)
        for key, value in update_data.items():
            setattr(orm, key, value)
        if horas_data is not None:
            orm.horas.clear()
            for h in horas_data:
                orm.horas.append(TarifaHoraORM(**h))
        await self.session.flush()
        await self.session.refresh(orm, ["horas"])
        return orm

    async def delete(self, id_: int) -> bool:
        orm = await self.session.get(TarifaORM, id_)
        if orm is None:
            return False
        await self.session.delete(orm)
        await self.session.flush()
        return True
