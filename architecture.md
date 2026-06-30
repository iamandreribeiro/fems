# Arquitetura do Backend — FEMS

> Documento de decisão arquitetural (ADR consolidado) para acompanhar a migração
> ao Claude Code. Registra as decisões das Fases 2–3 e as fronteiras preparadas
> para as Fases 4–5 (IoT/agentes).
>
> Leia junto com [`spreadsheet-schema.md`](./spreadsheet-schema.md) (fonte de
> verdade do domínio) e [`design-system.md`](./design-system.md) (as 5 fases).

## Sumário das decisões

| # | Tema | Decisão |
|---|---|---|
| AD-1 | Série temporal | **Recomputar on-demand** com seed determinística. Materialização só como snapshot/cache explícito. Tabela separada reservada p/ série medida (Fase 4). |
| AD-2 | Arquitetura | **Monolito modular** com fronteiras alinhadas às camadas e prontas p/ extração. Não microsserviços agora. |
| AD-3 | DDD | **Leve** no geral; **domínio rico** apenas no motor de simulação. |
| AD-4 | Fluxo | Cliente envia **JSON de cadastro de fazenda**; backend **persiste o cadastro** e **recomputa a série** on-demand. |
| AD-5 | Resposta | Série horária completa (8.760 linhas) **ou** resumo agregado, conforme o endpoint. |

---

## AD-1 — Série temporal: recomputar com seed

A série horária (consumo / geração / custo) é **100% derivável** de
`(cadastro da fazenda + catálogo + clima + tarifa + seed)`. Ninguém a edita à mão.

- **Padrão:** recomputar sob demanda a partir de uma **seed determinística**
  gravada no cadastro da fazenda. Mesma fazenda + mesmo ano + mesma seed →
  sempre o mesmo resultado. Isto substitui o `RANDBETWEEN(85,115)` da planilha
  por um PRNG com seed.
- **Materialização:** opcional, só como **snapshot nomeado** somente-leitura
  (ex.: congelar "baseline 2025" para dashboard/artigo). Não é o caminho padrão
  e evita o passivo de invalidação de cache.
- **Série medida (Fase 4+):** quando os sensores IoT chegarem, a leitura real
  **não é derivável** e será sempre persistida, em tabela própria append-only.
  Simulado e medido compartilham o mesmo formato de leitura para comparação via `JOIN`.

**Premissa que sustenta a decisão:** a série simulada nunca recebe entrada manual
(override de uma hora específica). Se isso mudar, reavaliar em favor de materialização.

## AD-2 — Monolito modular preparado para extração

Time pequeno, fase de pesquisa, domínio ainda em evolução → microsserviços agora
cobram o pedágio (deploy distribuído, comunicação, transações, observabilidade)
antes do benefício. E ainda não se sabe *onde* cortar os serviços.

Organizar o monolito pelas mesmas fronteiras que virariam serviços, alinhadas às
camadas da planilha. Cada módulo tem fronteira explícita (pasta própria, entidades
próprias, comunicação por interface — **sem acesso direto às tabelas alheias**).

```
┌─────────────────────────────────────────────────────────┐
│                      API (REST / JSON)                    │
├───────────────┬───────────────┬───────────────┬──────────┤
│  Catálogo /   │   Cadastro    │   Simulação   │ Resultados│
│ Configuração  │  (instância)  │   (MOTOR)     │ Faturamen.│
│               │               │  domínio rico │           │
│ equipamentos  │ fazendas      │ fórmulas →    │ agregação │
│ perfis        │ cargas inst.  │ funções puras │ custo     │
│ geração (cfg) │               │ + seed        │ ponta/fp  │
│ tarifa        │               │               │           │
├───────────────┴───────────────┴───────────────┴──────────┤
│        [Fase 4+] Ingestão IoT — demarcado, vazio          │
│        (série MEDIDA via LoRaWAN, append-only)            │
└───────────────────────────────────────────────────────────┘
                          │
                   PostgreSQL
```

Quando a Fase 4 chegar, o módulo de Ingestão IoT pode ser extraído sem reescrever
o resto.

## AD-3 — DDD na dose certa

- **Catálogo, Cadastro, Resultados:** essencialmente CRUD estruturado.
  Entidades + serviços de aplicação. Sem cerimônia.
- **Motor de Simulação:** concentra toda a lógica de negócio real → **domínio rico**.
  Funções puras, testáveis isoladas, **validadas contra o baseline da planilha**.
  Value objects se pagam aqui: `Tarifa`, `PerfilHorario`, `CapacidadeBateria`,
  `Seed`. Regras que vivem aqui:
  - geração eólica usa **estrutura normalizada igual à solar** (vento÷vento_ref×
    capacidade, com clamp min/max) — **não** curva cúbica;
  - bateria descarrega `Cons_Min` **cheio por hora de ponta** (não distribuído);
  - clamp `MIN(Gen_Max, MAX(Gen_Min, …))` e cutoff mínimo;
  - ruído estocástico ±15% via PRNG com seed.

---

## Fluxo de requisição (AD-4 / AD-5)

```
Cliente (Postman → futuramente frontend em steps)
   │  POST /fazendas  { JSON de cadastro }
   ▼
[Cadastro] valida + persiste a fazenda (+ seed)        ── grava (pequeno, estável)
   │
   ▼
[Simulação] recompõe a série a partir de
   cadastro + catálogo + clima + tarifa + seed          ── NÃO grava (derivado)
   │
   ▼
[Resultados] agrega (custo, ponta/fora-ponta, mensal)
   │
   ▼
Resposta:  série horária completa  OU  resumo agregado
```

### Contrato do payload (cadastro de fazenda)

Dois modos previstos (override só estrutural agora, implementação futura):

```jsonc
{
  "fazenda": {
    "nome": "Fazenda Boa Vista",
    "tamanho_ha": 80,
    "tipo": "Pequena",                  // Pequena | Média  → resolve Qtd_Peq/Qtd_Med
    "areas": {                          // flags → ativa/inativa cargas
      "escritorio": true,
      "cozinha": true,
      "quarto": true,
      "irrigacao": true
    },
    "geracao": {
      "solar":  "SOL-PEQ",              // id do catálogo Config_Geracao (ou null)
      "eolica": "EOL-PEQ",              // (ou null)
      "bateria": "BAT-001"              // (ou null)
    },
    "tarifa": "AZUL_HOROSSAZONAL",
    "seed": 20250101,                   // determinismo da série
    "ano": 2025
  },

  // MODO OVERRIDE (futuro — Fase de evolução "usuário informa equipamentos").
  // Ausente = modo baseline (resolve tudo do catálogo).
  "overrides": {
    "equipamentos": [ /* equipamentos customizados que sobrescrevem o baseline */ ],
    "perfis": [ /* perfis horários próprios */ ]
  }
}
```

**Eixos do modelo** (esclarecimento de simetria):

- `Config_Equipamentos` → **INPUT de catálogo** (configuração administrável,
  seed do banco; normalmente *não* viaja no payload de fazenda).
- `Geração` e `Cargas` → **OUTPUT derivado** (o motor produz; o cliente recebe,
  nunca envia).

### Endpoints (rascunho para validação no Postman)

| Método | Rota | Faz |
|---|---|---|
| `POST` | `/fazendas` | Persiste cadastro + retorna resumo agregado |
| `GET`  | `/fazendas/{id}` | Lê o cadastro persistido |
| `GET`  | `/fazendas/{id}/simulacao` | Recomputa e retorna **série horária completa** (8.760 linhas) |
| `GET`  | `/fazendas/{id}/resumo` | Recomputa e retorna **resumo agregado** (mensal/custo) |
| `GET`  | `/catalogo/equipamentos` | Lista o catálogo (admin) |
| `POST` | `/snapshots` | (opcional) Materializa um cenário nomeado |

> **Nota de payload:** a série completa são ~8.760 linhas/fazenda (poucos MB em
> JSON). Por isso o resumo vive em rota separada — valide o barato primeiro,
> baixe a série inteira só quando precisar.

---

## Esboço de schema PostgreSQL

> DDL ilustrativo — a versão executável (migrations) será gerada na IDE.

### Camada Configuração (catálogo, seed administrável)

```sql
-- equipamentos padrão + perfil horário (24 fatores)
CREATE TABLE config_equipamento (
  id            TEXT PRIMARY KEY,        -- ESC-01, IRR-01...
  area          TEXT NOT NULL,           -- Escritório, Cozinha, Quarto, Irrigação/Lavoura
  equipamento   TEXT NOT NULL,
  potencia_kw   NUMERIC NOT NULL,
  qtd_peq       NUMERIC NOT NULL,
  qtd_med       NUMERIC NOT NULL,
  perfil_horario NUMERIC[24] NOT NULL    -- fatores 0..1 por hora
);

CREATE TABLE config_geracao (
  id              TEXT PRIMARY KEY,      -- SOL-PEQ, EOL-MED...
  tipo            TEXT NOT NULL,         -- 'Solar FV' | 'Eólica'
  pot_nominal_kwp NUMERIC NOT NULL,
  eficiencia_pct  NUMERIC NOT NULL,
  ref_conversao   NUMERIC NOT NULL,      -- GHI ref (W/m²) ou vento ref (m/s)
  gen_max_kw      NUMERIC NOT NULL,
  gen_min_kw      NUMERIC NOT NULL
);

CREATE TABLE config_tarifa (
  nome      TEXT NOT NULL,               -- 'AZUL_HOROSSAZONAL'
  hora      SMALLINT NOT NULL,           -- 0..23
  preco_kwh NUMERIC NOT NULL,
  tipo      TEXT NOT NULL,               -- 'Ponta' | 'Fora Ponta'
  PRIMARY KEY (nome, hora)
);
```

### Camada Cadastro (instância — PERSISTIDO)

```sql
CREATE TABLE fazenda (
  id          TEXT PRIMARY KEY,          -- FAZ-001
  nome        TEXT NOT NULL,
  tamanho_ha  NUMERIC NOT NULL,
  tipo        TEXT NOT NULL,             -- 'Pequena' | 'Média'
  tem_escritorio BOOLEAN NOT NULL,
  tem_cozinha    BOOLEAN NOT NULL,
  tem_quarto     BOOLEAN NOT NULL,
  tem_irrigacao  BOOLEAN NOT NULL,
  id_solar    TEXT REFERENCES config_geracao(id),
  id_eolica   TEXT REFERENCES config_geracao(id),
  id_bateria  TEXT,
  tarifa      TEXT NOT NULL,
  seed        BIGINT NOT NULL,           -- determinismo
  ano         SMALLINT NOT NULL,
  criado_em   TIMESTAMPTZ DEFAULT now()
);

-- cargas instanciadas: podem ser derivadas do cadastro (não precisam persistir),
-- mas a tabela existe se você quiser inspecioná-las / permitir override futuro.
CREATE TABLE fazenda_carga (
  fazenda_id   TEXT REFERENCES fazenda(id),
  carga        TEXT NOT NULL,            -- Pivô, Bomba_Aux, Escritório...
  tipo         TEXT NOT NULL,            -- Agrícola | Sede | Armazenamento
  cons_max_kw  NUMERIC NOT NULL,
  cons_min_kw  NUMERIC NOT NULL,
  status       TEXT NOT NULL,            -- Ativo | Inativo
  PRIMARY KEY (fazenda_id, carga)
);
```

### Camada Simulação/Resultados (DERIVADA — não persistida por padrão)

```sql
-- NÃO existe tabela de série simulada no caminho padrão (recompute on-demand).
-- Opcional: snapshot nomeado, somente-leitura.
CREATE TABLE snapshot_simulacao (
  id          BIGSERIAL PRIMARY KEY,
  fazenda_id  TEXT REFERENCES fazenda(id),
  nome        TEXT NOT NULL,             -- 'baseline-2025'
  seed        BIGINT NOT NULL,
  criado_em   TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE snapshot_serie (
  snapshot_id BIGINT REFERENCES snapshot_simulacao(id),
  data_hora   TIMESTAMPTZ NOT NULL,
  consumo_kwh NUMERIC, geracao_kwh NUMERIC,
  bateria_descarga_kwh NUMERIC, saldo_liquido_kwh NUMERIC,
  tarifa_rs NUMERIC, custo_rs NUMERIC, tipo_horario TEXT,
  PRIMARY KEY (snapshot_id, data_hora)
);

-- [Fase 4+] série MEDIDA (sensores) — append-only, mesma forma de leitura
CREATE TABLE leitura_medida (
  fazenda_id  TEXT REFERENCES fazenda(id),
  data_hora   TIMESTAMPTZ NOT NULL,
  consumo_kwh NUMERIC, geracao_kwh NUMERIC,
  fonte       TEXT,                      -- id do sensor/gateway LoRaWAN
  PRIMARY KEY (fazenda_id, data_hora)
);
```

---

## Ordem de implementação sugerida (para o plano na IDE)

1. **Catálogo** — seed das tabelas de configuração a partir da planilha v8.
2. **Cadastro** — `POST /fazendas` + persistência + derivação de `fazenda_carga`.
3. **Motor de Simulação** — funções puras (perfil → consumo, clima → geração,
   bateria, custo), com seed. **Validar contra o baseline da planilha.**
4. **Resultados** — agregações + endpoints `/simulacao` e `/resumo`.
5. **(Fase 4)** módulo de Ingestão IoT — só quando o hardware chegar.

## Itens em aberto

- Escolha de stack/linguagem do backend (a definir na IDE).
- Geração da série completa de **8.760 h** (a planilha v8 popula só ~1 mês a jusante).
- Estratégia de teste de validação: comparar saída do motor com o baseline da v8.
