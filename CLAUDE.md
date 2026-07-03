# CLAUDE.md

Guia para o Claude Code trabalhar neste repositório. Mantenha conciso e atualizado.

## O que é este projeto

**Farm Energy Management System (FEMS)** — sistema de gestão energética para
fazendas de grãos (soja e milho) no **Cerrado Goiano**. A lacuna de pesquisa
sendo endereçada: a literatura de EMS concentra-se em contextos
residenciais/urbanos, deixando o meio rural/agrícola subatendido.

O projeto tem duas dimensões em paralelo:

- **Acadêmica:** artigo formal em português, normas ABNT.
- **Software/hardware:** arquitetura IoT multiagente em desenvolvimento.

### Fazendas de referência

- **Fazenda Boa Vista** — 80 ha, porte Pequena (FAZ-001).
- **Fazenda São Pedro** — 320 ha, porte Média (FAZ-002).

### Contexto de domínio

- Tarifa **Azul horossazonal** (Enel/Equatorial Goiás), **ponta 18h–21h**.
- Calendário agrícola: colheita soja jan–mar, milho safrinha jun–jul,
  pré-plantio out–nov.
- Cargas de irrigação via **pivô central**; padrões de irradiação/clima do Cerrado.

## Estado atual (5 fases)

1. **Fase 1 (completa):** protótipo paramétrico em Excel.
   `modelo_gestao_energia_fazenda_v8.xlsx` — 11 abas, simulação horária, 4 áreas
   de carga (Escritório, Cozinha, Quarto, Irrigação/Lavoura).
2. **Fases 2–3 (implementadas):** backend FastAPI + SQLAlchemy async + PostgreSQL.
   Schema reconciliado com a planilha (catálogo `config_equipamento` com
   qtd_peq/qtd_med + perfil inline; geração com parâmetros tipados; tarifa horária
   Ponta/Fora-Ponta) + cadastro (`fazenda` + `fazenda_cargas` derivadas). Motor de
   simulação puro em `domain/simulation/` (série de 8.760 h, PRNG com seed),
   **validado contra o baseline de janeiro da v8** (geração/bateria batem exato).
   API `/v1/fazendas` (+ `/simulacao`, `/resumo`) e CLI `scripts/gerar_dataset.py`
   (saída Parquet) chamam o mesmo `simular_fazenda`. Monolito modular, DDD leve.
3. **Fases 4–5 (planejadas):** arquitetura IoT distribuída multiagente —
   LoRaWAN, protocolo FIPA-ACL, paradigma CTDE (treino centralizado, execução
   descentralizada).

## Documentos-chave

- [`docs/spreadsheet-schema.md`](docs/spreadsheet-schema.md) — **fonte de verdade**
  da estrutura da planilha v8 (abas, colunas, fórmulas). Base para o schema do
  banco e as regras de negócio. **Leia antes de mexer no backend.**
- [`docs/design-system.md`](docs/design-system.md) — documento de design (SDD),
  as 5 fases e decisões arquiteturais.
- `modelo_gestao_energia_fazenda_v8.xlsx` — artefato de simulação versionado.

## Arquitetura do modelo (resumo)

Quatro camadas, espelhadas no software planejado:

```
Configuração (imutável)  →  Cadastro (instância)  →  Simulação (derivada)  →  Resultados (derivada)
Config_Equipamentos          Cadastro_Fazenda          Base_Irradiacao            Consumo_Fatura
Perfil_Area                  Cadastro_Cargas           Geracao                    Resumo_Mensal
Config_Geracao                                         Cargas
Tarifa
```

Fluxo de desenvolvimento iterativo, camada por camada:
**configuração → cadastro → simulação → resultados.**

## Princípios (NÃO violar)

1. **Design paramétrico:** o cadastro de fazenda é a fonte de verdade única.
   Nova fazenda = nova linha em `Cadastro_Fazenda`; o resto se propaga. No
   backend, preservar essa propriedade.
2. **Seguir a referência exatamente:** espelhar a metodologia real da planilha,
   não substituir por fórmulas de domínio genéricas. (Ex.: geração eólica usa a
   **mesma estrutura normalizada** da solar — vento÷vento_ref×capacidade com
   clamp — e **não** curva cúbica de potência.)
3. **Fórmulas → funções determinísticas:** cada coluna calculada vira função
   pura. O ruído `RANDBETWEEN(85,115)` deve usar **seed** para reprodutibilidade.
4. **Bateria é uma carga** (`Tipo = Armazenamento`), não entidade especial.
   Descarga aplica `Cons_Min` cheio **por hora de ponta** (não distribuído).
5. **Excel não é descartável:** a estrutura do workbook informa diretamente o SDD
   e o schema do banco. A simulação bottom-up de 8.760 h é o baseline de
   validação para o comportamento futuro dos agentes.
6. **Entregar artefatos completos e prontos para uso** (workbooks/seções
   inteiras), não esboços parciais.

## Ferramentas

- **Excel / openpyxl:** geração programática com formatação estilizada,
  destaque condicional das horas de ponta, agregações por fórmula.
- **PostgreSQL:** camada de banco planejada.
- **LoRaWAN + FIPA-ACL:** stack de comunicação dos agentes.
- Referências regulatórias: ANEEL, Tarifa Azul; classificação INCRA.

## Itens em aberto / a verificar

- **Quirk fiel reproduzido:** `Cons_Max = MAX(perfil[00h], perfil[01h], perfil[11h])`
  — só 3 colunas (C, D, N da fórmula), **não** o pico das 24 h. Mantido por fidelidade
  (princípio 2). Ver `domain/instance/instanciar.py`.
- **Porte Grande** usa `qtd_grande` + geradores `SOL-GRD`/`EOL-GRD` — valores **propostos**
  (não vêm da planilha v8), ajustáveis em `scripts/_extract_from_xlsx.py`.
- **Cadastro personalizado:** override parcial (qtd/potência/perfil) via `overrides` no
  payload; resolvido antes do `Perfil_Area` em `domain/instance/resolver.py`.
- Snapshots materializados + ingestão IoT (Fases 4–5) — fronteiras demarcadas, vazias.
- `uv.lock`: regerar com `uv sync` após a adição de `pyarrow`/`openpyxl`/`matplotlib`.
- Artigo: verificar transição Enel→Equatorial Goiás, valores de módulo fiscal
  INCRA, e confirmação de DOI de preprints recentes.
