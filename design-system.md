# Design System — Farm Energy Management System (FEMS)

> Documento de design da evolução do protótipo em planilha para um backend
> escalável. Versão revisada e reestruturada a partir do `.docx` original.

## Contexto

Estamos evoluindo uma planilha estruturada em múltiplas camadas para um sistema
backend escalável. A planilha atual (ver [`spreadsheet-schema.md`](./spreadsheet-schema.md))
já implementa:

- **Camada de configuração** parametrizável (cargas padrão, perfis horários, geração e tarifas)
- **Camada de cadastro** com fórmulas encadeadas
- **Camada de simulação** com dados sintéticos (base climática + consumo + geração)
- **Camada de resultados** (consumo, custo e agregações mensais)

Essa estrutura deve ser traduzida para um modelo de software onde o comportamento
atual (derivado de fórmulas) seja reproduzido via **regras de negócio determinísticas**.

## Objetivo do sistema (fase inicial)

Construir o **dataset base (baseline)** que servirá como referência para todas as
simulações futuras. Esse dataset deve:

- Representar os equipamentos padrão (cargas)
- Conter perfis de consumo validados por tipo de ambiente
- Permitir expansão (novos equipamentos, perfis, cenários)
- Servir como base para a geração automática de consumo por fazenda

---

## Fase 1 — Dataset Base (Baseline)

### 1.1 Cadastro de Cargas Padrão

Conjunto fixo inicial de equipamentos. Atributos:

- `nome`
- `potência` (kW)
- `área` (escritório, cozinha, quarto, irrigação/lavoura)
- `quantidade padrão por porte` (pequena / média)
- `perfil horário associado` (24 fatores 0–1)

### 1.2 Perfis de Consumo (`Perfil_Horario`)

- Curvas normalizadas (0–1) por hora (24 h)
- Associadas a tipos de ambiente
- Exemplos: Escritório (uso diurno 7h–18h); Cozinha (picos em refeições);
  Quarto (uso noturno); Irrigação (madrugada/fora-ponta).

### 1.3 Configuração de Geração

- Tipos: **Solar FV** e **Eólica**
- Parâmetros: potência nominal (kWp), eficiência, referência de conversão,
  geração máx/mín (clamp), dependência climática (irradiância GHI / vento).
- **Eólica usa a mesma estrutura normalizada da solar** (vento ÷ vento de
  referência × capacidade, com clamp), não curva cúbica genérica.

### 1.4 Tarifa

- Modelo: **Tarifa Azul horossazonal** (Ponta vs Fora-Ponta).
- Estrutura: hora, valor por kWh, tipo de horário.
- Ponta: 18h–20h (R$ 1,1039/kWh); Fora-Ponta (R$ 0,6813/kWh).

---

## Fase 2 — Cadastro de Fazenda

Permitir que o sistema gere automaticamente o dataset de uma fazenda a partir do baseline.

**Entrada do usuário:** nome, tipo (pequena/média), áreas ativas (flags),
possui geração? (sim/não + tipo), tarifa aplicada.

**Processamento:**

- Instanciar cargas a partir do catálogo de cargas padrão
- Ajustar quantidades conforme o tipo da fazenda
- Filtrar por áreas ativas
- Associar perfis de consumo automaticamente

---

## Fase 3 — Geração Automática de Consumo

A partir de cargas, perfis horários, quantidade e potência, gerar:

- consumo horário (kWh)
- distribuição por área
- variação temporal (ruído estocástico simulando comportamento real)

---

## Fase 4 — Geração de Dataset Sintético

Incorporar variáveis externas: irradiância (solar), temperatura, vento, sazonalidade. Gerar:

- produção energética (solar/eólica)
- impacto no consumo líquido
- comportamento mensal

---

## Fase 5 — Resultado e Cálculo de Custo

Calcular:

- consumo líquido (`consumo − geração − descarga de bateria`)
- custo horário (baseado na tarifa)
- agregações: diário, mensal, por área

---

## Evolução do Produto (visão futura)

Após o dataset base estar sólido, o fluxo do usuário final:

1. Usuário informa os equipamentos que possui.
2. Sistema encontra equivalentes no dataset base e aplica perfis existentes.
3. Resultado: gera automaticamente um perfil energético personalizado.

---

## Decisões arquiteturais

- **Evitar lógica hardcoded** → tudo vem da camada de configuração.
- **Fórmulas da planilha → funções determinísticas** no backend (com seed para
  o ruído estocástico, garantindo reprodutibilidade).
- **Separação clara de camadas:**
  - Configuração (imutável / administrável / versionável)
  - Instância (fazenda)
  - Simulação (derivada)
  - Resultados (derivada)
- **Bateria é modelada como carga** do tipo `Armazenamento`, não como entidade
  especial — mantém o modelo consistente e extensível.

### Capacidades-alvo do backend

- Cadastrar e **versionar** datasets base
- Instanciar fazendas automaticamente a partir do baseline
- Gerar consumo e geração por hora (série de 8.760 h)
- Calcular custo energético (tarifa horossazonal + descarga de bateria na ponta)
- Servir como base para futuras interfaces (web/app)
