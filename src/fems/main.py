from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from fems.api.v1 import equipamentos, fazendas, geracoes, tarifas
from fems.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


app = FastAPI(
    title="FEMS — Farm Energy Management System",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(equipamentos.router, prefix="/v1")
app.include_router(geracoes.router, prefix="/v1")
app.include_router(tarifas.router, prefix="/v1")
app.include_router(fazendas.router, prefix="/v1")
