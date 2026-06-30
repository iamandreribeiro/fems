from fastapi import APIRouter, HTTPException, status

from fems.api.deps import SessionDep
from fems.domain.configuration.equipamento import (
    Equipamento,
    EquipamentoCreate,
    EquipamentoUpdate,
)
from fems.services.equipamento_service import EquipamentoService

router = APIRouter(prefix="/equipamentos", tags=["equipamentos"])


@router.post("", response_model=Equipamento, status_code=status.HTTP_201_CREATED)
async def create_equipamento(data: EquipamentoCreate, session: SessionDep) -> Equipamento:
    return await EquipamentoService(session).create(data)


@router.get("", response_model=list[Equipamento])
async def list_equipamentos(session: SessionDep) -> list[Equipamento]:
    return await EquipamentoService(session).list()


@router.get("/{id_}", response_model=Equipamento)
async def get_equipamento(id_: str, session: SessionDep) -> Equipamento:
    result = await EquipamentoService(session).get_by_id(id_)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Equipamento not found")
    return result


@router.patch("/{id_}", response_model=Equipamento)
async def update_equipamento(id_: str, data: EquipamentoUpdate, session: SessionDep) -> Equipamento:
    result = await EquipamentoService(session).update(id_, data)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Equipamento not found")
    return result


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipamento(id_: str, session: SessionDep) -> None:
    deleted = await EquipamentoService(session).delete(id_)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Equipamento not found")
