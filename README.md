# FEMS — Farm Energy Management System

Backend de simulação energética rural. Evoluído a partir de uma planilha multi-camada (configuração / instância / simulação) para um sistema escalável.

Veja o [design doc](./Design_System_-_Farm_Energy_Management_System.md) para o contexto completo.

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes Python)
- Docker + Docker Compose (para Postgres local)

Instalar uv (se ainda não tiver):

```powershell
python -m pip install --user uv
```

## Setup local

```powershell
# 1. Clonar e entrar na pasta
cd fems

# 2. Subir o Postgres (host: 127.0.0.1:5433 → container: 5432)
docker compose up -d

# 3. Instalar deps + criar venv (.venv)
uv sync

# 4. Configurar variáveis de ambiente
copy .env.example .env

# 5. Aplicar migrações (cria as tabelas de configuração + cadastro)
uv run alembic upgrade head

# 6. Popular o catálogo baseline (equipamentos, geração, tarifa) extraído da planilha v8
uv run python scripts/seed_catalog.py

# 7. Subir a API em modo dev
uv run uvicorn fems.main:app --reload
```

A API ficará em `http://localhost:8000`. Docs OpenAPI em `http://localhost:8000/docs`.

### Endpoints principais

| Método | Rota | Faz |
|---|---|---|
| `POST` | `/v1/fazendas` | Persiste o cadastro + deriva e grava as cargas instanciadas |
| `GET` | `/v1/fazendas/{id}` | Lê o cadastro persistido (com cargas) |
| `GET` | `/v1/fazendas/{id}/resumo` | Recomputa e retorna o resumo mensal (12 linhas) |
| `GET` | `/v1/fazendas/{id}/simulacao` | Recomputa e retorna a série horária (8.760 linhas) |
| `GET/POST/...` | `/v1/equipamentos`, `/v1/geracoes`, `/v1/tarifas` | CRUD do catálogo (admin) |

## Gerar um dataset (CLI, sem banco)

O mesmo motor de simulação da API, via linha de comando, lendo um JSON de cadastro
(igual ao payload de `POST /fazendas`) e gravando o dataset em Parquet:

```powershell
uv run python scripts/gerar_dataset.py --config tests/fixtures/faz_001.json --output out/
```

Gera `out/consumo_fatura.parquet` (8.760 linhas), `out/resumo_mensal.parquet` (12 meses)
e `out/cadastro_cargas.parquet`. O catálogo vem de `fems.data.catalog_seed` e o clima de
`fems.data` (base canônica 2025) — não precisa de banco.

> A base climática e o `catalog_seed.py` são gerados de `modelo_gestao_energia_fazenda_v8.xlsx`
> por `scripts/_extract_from_xlsx.py` (dev-only, requer openpyxl). O runtime não lê o .xlsx.

## Comandos úteis

| Comando | O que faz |
|---|---|
| `uv sync` | Instala/atualiza deps conforme `uv.lock` |
| `uv add <pkg>` | Adiciona dep de runtime |
| `uv add --dev <pkg>` | Adiciona dep de dev |
| `uv run pytest` | Roda testes |
| `uv run ruff check .` | Lint |
| `uv run ruff format .` | Formata código |
| `uv run mypy src/` | Type check estrito |
| `uv run alembic revision --autogenerate -m "msg"` | Gera nova migração |
| `uv run alembic upgrade head` | Aplica migrações |
| `uv run python scripts/seed_catalog.py` | Popula o catálogo baseline no banco |
| `uv run python scripts/gerar_dataset.py --config <f.json> --output out/` | Gera o dataset (Parquet) |
| `uv run python scripts/_extract_from_xlsx.py` | (dev) Regenera clima + `catalog_seed.py` do .xlsx |
| `docker compose up -d` | Sobe Postgres |
| `docker compose down` | Para Postgres (preserva volume) |
| `docker compose down -v` | Para Postgres e apaga volume |

## Estrutura

```
src/fems/
├── core/              # Config, DB, logging
├── domain/            # Lógica de negócio pura (sem I/O)
│   ├── configuration/   # Equipamentos, geração, tarifa (modelos Pydantic + enums)
│   ├── instance/        # Fazenda + Perfil_Area + instanciação de cargas
│   └── simulation/      # Motor: tipos, prng, geração, consumo, bateria, custo, resumo, engine
├── data/              # Catálogo baseline (catalog_seed.py) + clima (json.gz) e loaders
├── repositories/      # Acesso a dados (SQLAlchemy ORM)
├── services/          # Casos de uso / orquestração (+ seed, mapeamento ORM→motor)
├── api/v1/            # FastAPI routes
└── main.py            # App entry
scripts/               # CLI: gerar_dataset, seed_catalog, _extract_from_xlsx (dev)
tests/
├── unit/              # Testes do domínio + motor (sem DB)
├── test_baseline.py   # Validação do motor vs baseline de janeiro da planilha v8
└── integration/       # Testes de API end-to-end (requer Postgres + DB fems_test)
```

Princípio: `domain/` é Python puro — não importa SQLAlchemy nem FastAPI. O motor de
simulação (`domain/simulation/engine.py:simular_fazenda`) é o ponto único de reuso:
tanto a API quanto a CLI o chamam. Lógica testável sem subir infra.

## Porta do Postgres

O Postgres do Docker está mapeado em `127.0.0.1:5433` (não 5432) para evitar conflito caso você tenha um Postgres nativo instalado. Se quiser usar 5432, edite `docker-compose.yml` e `.env`/`.env.example` juntos.

## Status

Camadas de configuração, cadastro (fazenda + cargas), simulação (série de 8.760 h) e
resultados (fatura + resumo mensal) implementadas e validadas contra o baseline de
janeiro da planilha v8 (geração/bateria batem exato; consumo dentro de ±3% do ruído).
Entregues os dois objetivos: **banco** que guarda o estado da fazenda e **script**
que gera o dataset. Próximos passos: snapshots materializados e ingestão IoT (Fases 4–5).

> **Lockfile:** `pyarrow` (runtime) e `openpyxl` (dev) foram adicionados ao `pyproject.toml`.
> Rode `uv sync` (ou `uv lock`) para atualizar o `uv.lock`.
