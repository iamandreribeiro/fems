from fastapi import APIRouter, HTTPException, status

from fems.api.deps import SessionDep
from fems.domain.instance.fazenda import FazendaCreate, FazendaRead
from fems.domain.instance.resultado import (
    FaturaHoraOut,
    RankingItemOut,
    RankingOut,
    ResumoMesOut,
)
from fems.services.fazenda_service import CatalogoIncompletoError, FazendaService

router = APIRouter(prefix="/fazendas", tags=["fazendas"])


@router.post("", response_model=FazendaRead, status_code=status.HTTP_201_CREATED)
async def create_fazenda(data: FazendaCreate, session: SessionDep) -> FazendaRead:
    try:
        return await FazendaService(session).create(data)
    except CatalogoIncompletoError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.get("", response_model=list[FazendaRead])
async def list_fazendas(session: SessionDep) -> list[FazendaRead]:
    return await FazendaService(session).listar()


@router.get("/{id_}", response_model=FazendaRead)
async def get_fazenda(id_: str, session: SessionDep) -> FazendaRead:
    result = await FazendaService(session).get_by_id(id_)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda not found")
    return result


@router.get("/{id_}/simulacao", response_model=list[FaturaHoraOut])
async def simular_fazenda_endpoint(id_: str, session: SessionDep) -> list[FaturaHoraOut]:
    fatura = await FazendaService(session).simulacao(id_)
    if fatura is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda not found")
    return [FaturaHoraOut.model_validate(f) for f in fatura]


@router.get("/{id_}/resumo", response_model=list[ResumoMesOut])
async def resumo_fazenda(id_: str, session: SessionDep) -> list[ResumoMesOut]:
    resumo = await FazendaService(session).resumo(id_)
    if resumo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda not found")
    return [ResumoMesOut.model_validate(r) for r in resumo]


@router.get("/{id_}/ranking-equipamentos", response_model=RankingOut)
async def ranking_equipamentos(id_: str, session: SessionDep) -> RankingOut:
    ranking = await FazendaService(session).ranking(id_)
    if ranking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda not found")
    por_area = {
        area.value: [RankingItemOut.model_validate(item) for item in itens]
        for area, itens in ranking.items()
    }
    return RankingOut(por_area=por_area)


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fazenda(id_: str, session: SessionDep) -> None:
    deleted = await FazendaService(session).delete(id_)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda not found")
