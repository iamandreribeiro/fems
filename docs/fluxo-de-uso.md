# Fluxo de uso — criar a fazenda e gerar o dataset

Fluxo ponta-a-ponta para o uso corrente do sistema: **cadastra a fazenda no frontend**
e **gera o dataset (Parquet) pela CLI, por id** — sem escrever nenhum arquivo de config
na mão.

## Pré-requisitos

Backend e frontend no ar:

```powershell
# backend (repo fems)
docker compose up -d
uv run alembic upgrade head
uv run python scripts/seed_catalog.py     # só na 1ª vez (popula o catálogo)
uv run uvicorn fems.main:app --reload      # API em http://localhost:8000

# frontend (repo fems-ui)
pnpm dev                                    # UI em http://localhost:5173
```

## 1. Criar a fazenda (no front)

Em **http://localhost:5173** → **Nova fazenda** → preencha e salve. A fazenda fica
persistida no banco, já com as cargas derivadas e os `overrides` (se houver).

## 2. Gerar o dataset (no terminal)

```powershell
uv run python scripts/gerar_dataset.py --fazenda-id FAZ-004 --output out/faz_004 --completo
```

**Dois lugares para trocar** (independentes entre si):

| Trecho | O que é | Exemplos |
|---|---|---|
| `--fazenda-id FAZ-004` | O **ID exato** da fazenda criada na UI (campo "ID" do formulário, **não** o nome) | `FAZ-007`, `MINHA-FAZ` |
| `--output out/faz_004` | A **pasta de saída** dos `.parquet` (criada se não existir; nome livre) | `out/sao_miguel` |

> A pasta **não** precisa ter o nome do ID — os dois são independentes. O `out/` na frente
> é só a convenção do projeto (essa pasta é ignorada pelo git).

Exemplo para a fazenda `FAZ-007`:

```powershell
uv run python scripts/gerar_dataset.py --fazenda-id FAZ-007 --output out/faz_007 --completo
```

Ao rodar por `--fazenda-id`, a CLI puxa **cadastro + overrides + catálogo** direto do
Postgres — reflete exatamente o que você criou/editou na UI.

## Detalhes

- **`--completo` é opcional:**
  - **Com:** gera as **7 tabelas** — as 4 principais + `equipamentos.parquet`,
    `consumo.parquet` (por carga × hora) e `geracao.parquet` (por gerador × hora).
  - **Sem:** gera só as **4 principais** — `consumo_fatura.parquet`, `resumo_mensal.parquet`,
    `cadastro_cargas.parquet`, `ranking_equipamentos.parquet`.
- **Não lembra o ID?** A lista em **http://localhost:5173** mostra o ID de cada fazenda
  na primeira coluna.
- **ID inexistente** → a CLI encerra com `erro: fazenda '<id>' não encontrada no banco`
  (sem stacktrace).

## Como abrir o dataset

Os arquivos ficam na pasta do `--output`. Em Python:

```python
import pandas as pd
df = pd.read_parquet("out/faz_004/consumo_fatura.parquet")
```

Parquet também abre direto em DBeaver, Power BI, DuckDB, etc.

## Alternativa: sem banco, a partir de um JSON

Quando você não quer persistir a fazenda (ex.: um cenário avulso), dá para passar os
parâmetros por um JSON (o mesmo payload de `POST /v1/fazendas`) em vez de `--fazenda-id`:

```powershell
uv run python scripts/gerar_dataset.py --config faz.json --output out/ --completo
```

Nesse modo o catálogo vem do módulo empacotado (`fems.data.catalog_seed`, offline); com
`--from-db` ele passa a vir do Postgres. `--fazenda-id` e `--config` são mutuamente exclusivos.
