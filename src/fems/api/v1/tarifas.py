from fastapi import APIRouter, HTTPException, status

from fems.api.deps import SessionDep
from fems.domain.configuration.tarifa import Tarifa, TarifaCreate, TarifaUpdate
from fems.services.tarifa_service import TarifaService

router = APIRouter(prefix="/tarifas", tags=["tarifas"])


@router.post("", response_model=Tarifa, status_code=status.HTTP_201_CREATED)
async def create_tarifa(data: TarifaCreate, session: SessionDep) -> Tarifa:
    return await TarifaService(session).create(data)


@router.get("", response_model=list[Tarifa])
async def list_tarifas(session: SessionDep) -> list[Tarifa]:
    return await TarifaService(session).list()


@router.get("/{id_}", response_model=Tarifa)
async def get_tarifa(id_: int, session: SessionDep) -> Tarifa:
    result = await TarifaService(session).get_by_id(id_)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarifa not found")
    return result


@router.patch("/{id_}", response_model=Tarifa)
async def update_tarifa(id_: int, data: TarifaUpdate, session: SessionDep) -> Tarifa:
    result = await TarifaService(session).update(id_, data)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarifa not found")
    return result


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tarifa(id_: int, session: SessionDep) -> None:
    deleted = await TarifaService(session).delete(id_)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tarifa not found")
