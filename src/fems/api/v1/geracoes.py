from fastapi import APIRouter, HTTPException, status

from fems.api.deps import SessionDep
from fems.domain.configuration.geracao import (
    ConfiguracaoGeracao,
    ConfiguracaoGeracaoCreate,
    ConfiguracaoGeracaoUpdate,
)
from fems.services.geracao_service import ConfiguracaoGeracaoService

router = APIRouter(prefix="/geracoes", tags=["geracoes"])


@router.post("", response_model=ConfiguracaoGeracao, status_code=status.HTTP_201_CREATED)
async def create_geracao(
    data: ConfiguracaoGeracaoCreate, session: SessionDep
) -> ConfiguracaoGeracao:
    return await ConfiguracaoGeracaoService(session).create(data)


@router.get("", response_model=list[ConfiguracaoGeracao])
async def list_geracoes(session: SessionDep) -> list[ConfiguracaoGeracao]:
    return await ConfiguracaoGeracaoService(session).list()


@router.get("/{id_}", response_model=ConfiguracaoGeracao)
async def get_geracao(id_: str, session: SessionDep) -> ConfiguracaoGeracao:
    result = await ConfiguracaoGeracaoService(session).get_by_id(id_)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ConfiguracaoGeracao not found")
    return result


@router.patch("/{id_}", response_model=ConfiguracaoGeracao)
async def update_geracao(
    id_: str, data: ConfiguracaoGeracaoUpdate, session: SessionDep
) -> ConfiguracaoGeracao:
    result = await ConfiguracaoGeracaoService(session).update(id_, data)
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ConfiguracaoGeracao not found")
    return result


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_geracao(id_: str, session: SessionDep) -> None:
    deleted = await ConfiguracaoGeracaoService(session).delete(id_)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "ConfiguracaoGeracao not found")
