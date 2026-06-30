"""Service de cadastro de fazenda + recompute da simulação on-demand.

Persiste o cadastro (pequeno, estável) e suas cargas derivadas; recomputa a série
horária / resumo sob demanda a partir de (catálogo + clima + seed). Tanto a API
quanto a CLI compartilham o mesmo motor `simular_fazenda`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from fems.data.clima import carregar_clima
from fems.domain.instance.fazenda import FazendaCreate, FazendaRead
from fems.domain.instance.instanciar import instanciar_cargas
from fems.domain.simulation.engine import simular_fazenda
from fems.domain.simulation.types import (
    Equipamento,
    FaturaHora,
    Gerador,
    ResumoMes,
    TarifaHora,
)
from fems.repositories.equipamento_repository import EquipamentoRepository
from fems.repositories.fazenda_repository import FazendaRepository
from fems.repositories.geracao_repository import ConfiguracaoGeracaoRepository
from fems.repositories.models import FazendaORM
from fems.repositories.tarifa_repository import TarifaRepository
from fems.services.sim_mapping import (
    carga_orm_from_instanciada,
    equipamento_from_orm,
    fazenda_spec_from_orm,
    gerador_from_orm,
    tarifa_hora_from_orm,
)


class CatalogoIncompletoError(RuntimeError):
    """Catálogo (equipamentos/geração/tarifa) ausente — rode o seed antes."""


class FazendaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FazendaRepository(session)
        self.equip_repo = EquipamentoRepository(session)
        self.ger_repo = ConfiguracaoGeracaoRepository(session)
        self.tarifa_repo = TarifaRepository(session)

    async def _equipamentos(self) -> list[Equipamento]:
        orms = await self.equip_repo.list()
        if not orms:
            raise CatalogoIncompletoError("catálogo de equipamentos vazio — rode seed_catalog")
        return [equipamento_from_orm(o) for o in orms]

    async def _geradores(self) -> dict[str, Gerador]:
        return {o.id: gerador_from_orm(o) for o in await self.ger_repo.list()}

    async def _tarifa(self, nome: str) -> list[TarifaHora]:
        orm = await self.tarifa_repo.get_by_nome(nome)
        if orm is None:
            raise CatalogoIncompletoError(f"tarifa '{nome}' não cadastrada")
        return [tarifa_hora_from_orm(h) for h in orm.horas]

    async def create(self, data: FazendaCreate) -> FazendaRead:
        equipamentos = await self._equipamentos()
        orm = FazendaORM(**data.model_dump())
        spec = fazenda_spec_from_orm(orm)
        cargas = instanciar_cargas(spec, equipamentos)
        carga_orms = [carga_orm_from_instanciada(orm.id, c) for c in cargas]
        await self.repo.create(orm, carga_orms)
        return FazendaRead.model_validate(orm)

    async def get_by_id(self, id_: str) -> FazendaRead | None:
        orm = await self.repo.get_by_id(id_)
        return FazendaRead.model_validate(orm) if orm else None

    async def listar(self) -> list[FazendaRead]:
        return [FazendaRead.model_validate(o) for o in await self.repo.list()]

    async def delete(self, id_: str) -> bool:
        return await self.repo.delete(id_)

    async def _simular(self, id_: str) -> tuple[list[FaturaHora], list[ResumoMes]] | None:
        orm = await self.repo.get_by_id(id_)
        if orm is None:
            return None
        spec = fazenda_spec_from_orm(orm)
        equipamentos = await self._equipamentos()
        geradores = await self._geradores()
        tarifa = await self._tarifa(spec.tarifa)
        clima = carregar_clima(spec.ano)
        result = simular_fazenda(spec, equipamentos, geradores, tarifa, clima)
        return result.fatura, result.resumo

    async def simulacao(self, id_: str) -> list[FaturaHora] | None:
        out = await self._simular(id_)
        return out[0] if out else None

    async def resumo(self, id_: str) -> list[ResumoMes] | None:
        out = await self._simular(id_)
        return out[1] if out else None
