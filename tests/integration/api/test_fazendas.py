"""Integração da API de fazendas contra Postgres (DB de teste `fems_test`).

Usa um engine próprio por teste (mesmo event loop do httpx.AsyncClient) e injeta a
sessão via dependency_overrides, evitando problemas de loop do asyncpg. Requer o
Postgres do docker-compose no ar e o DB de teste criado.
"""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fems.core.config import settings
from fems.core.database import Base, get_session
from fems.main import app
from fems.services.seed import seed_catalogo

PAYLOAD = {
    "id": "FAZ-001",
    "nome": "Fazenda Boa Vista",
    "tamanho_ha": 80,
    "tipo": "Pequena",
    "tem_escritorio": True,
    "tem_cozinha": True,
    "tem_quarto": True,
    "tem_irrigacao": True,
    "id_solar": "SOL-PEQ",
    "id_eolica": "EOL-PEQ",
    "id_bateria": "BAT-001",
    "tarifa": "AZUL_HOROSSAZONAL",
    "seed": 20250101,
    "ano": 2025,
}


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with session_factory() as s:
        await seed_catalogo(s)
        await s.commit()

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_post_persiste_cadastro_e_cargas(client: AsyncClient) -> None:
    r = await client.post("/v1/fazendas", json=PAYLOAD)
    assert r.status_code == 201, r.text
    body = r.json()
    cargas = {c["carga"]: c for c in body["cargas"]}
    assert float(cargas["Cozinha"]["cons_max_kw"]) == pytest.approx(0.354)
    assert float(cargas["Bateria"]["cons_max_kw"]) == 5.0
    assert cargas["Bomba_Aux"]["status"] == "Inativo"  # Qtd_Peq=0 na Pequena


async def test_get_e_resumo_recomputam(client: AsyncClient) -> None:
    await client.post("/v1/fazendas", json=PAYLOAD)

    r = await client.get("/v1/fazendas/FAZ-001")
    assert r.status_code == 200
    assert r.json()["nome"] == "Fazenda Boa Vista"

    r = await client.get("/v1/fazendas/FAZ-001/resumo")
    assert r.status_code == 200
    resumo = r.json()
    assert len(resumo) == 12
    jan = next(m for m in resumo if m["mes"] == 1)
    assert jan["geracao_kwh"] == pytest.approx(2244.029653, abs=1e-2)
    assert jan["bateria_descarga_kwh"] == pytest.approx(81.375, abs=1e-6)
    assert jan["consumo_kwh"] == pytest.approx(2315.19752, rel=0.03)


async def test_simulacao_retorna_8760_linhas(client: AsyncClient) -> None:
    await client.post("/v1/fazendas", json=PAYLOAD)
    r = await client.get("/v1/fazendas/FAZ-001/simulacao")
    assert r.status_code == 200
    assert len(r.json()) == 8760


async def test_get_inexistente_404(client: AsyncClient) -> None:
    r = await client.get("/v1/fazendas/NAO-EXISTE")
    assert r.status_code == 404
