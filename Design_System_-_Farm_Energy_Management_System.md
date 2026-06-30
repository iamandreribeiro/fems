# Sistema de Simulação Energética Rural

## Contexto

Estamos evoluindo uma planilha estruturada em múltiplas camadas para um sistema backend escalável.

A planilha atual já implementa:

- Camada de configuração parametrizável (cargas padrão, perfis horários, geração e tarifas)
- Camada de cadastro com fórmulas encadeadas
- Camada de simulação com dados sintéticos (base climática + consumo + geração)
- Camada de resultados (consumo, custo e agregações mensais)

Essa estrutura deve ser traduzida para um modelo de software onde o comportamento atual (derivado de fórmulas) seja reproduzido via regras de negócio.

## Objetivo do sistema (fase inicial)

Construir o **dataset base (baseline)** que servirá como referência para todas as simulações futuras.

Esse dataset deve:

- Representar os equipamentos padrão (cargas)
- Conter perfis de consumo validados por tipo de ambiente
- Permitir expansão (novos equipamentos, novos perfis, novos cenários)
- Servir como base para geração automática de consumo por fazenda

## Fase 1 — Configuração Base

### 1. Cadastro de Cargas Padrão

- Conjunto fixo inicial (ex: 23 equipamentos)
- Atributos:
  - nome
  - potência (W)
  - área (escritório, cozinha, quarto, irrigação)
  - quantidade padrão por porte (pequena/média)
  - perfil horário associado

### 2. Perfis de Consumo (Perfil_Horario)

- Curvas normalizadas (0–1) por hora (24h)
- Associadas a tipos de ambiente
- Exemplos:
  - Escritório: uso diurno (7h–18h)
  - Cozinha: picos em refeições
  - Quarto: uso noturno
  - Irrigação: 21h–6h

### 3. Configuração de Geração

- Tipos:
  - Solar FV
  - Eólica
- Parâmetros:
  - eficiência
  - curva de geração
  - dependência climática (irradiância, vento, etc.)

### 4. Tarifa

- Modelo inicial:
  - Tarifa horária (ex: ponta vs fora ponta)
- Estrutura:
  - horário início/fim
  - valor por kWh

## Fase 2 — Cadastro de Fazenda

Permitir que o sistema gere automaticamente o dataset de uma fazenda com base no baseline.

Entrada do usuário:

- Nome da fazenda
- Tipo (pequena/média)
- Áreas ativas (flags)
- Possui geração? (sim/não + tipo)
- Tarifa aplicada

Processamento:

- Instanciar cargas a partir do `Config_Cargas_Padrao`
- Ajustar quantidades conforme tipo da fazenda
- Filtrar por áreas ativas
- Associar perfis de consumo automaticamente

## Fase 3 — Geração Automática de Consumo

Com base nos dados:

- cargas
- perfis horários
- quantidade
- potência

Gerar:

- consumo horário (kWh)
- distribuição por área
- variação temporal (simulando comportamento real)

## Fase 4 — Geração de Dataset Sintético

Incorporar variáveis externas:

- irradiância (solar)
- temperatura
- vento
- sazonalidade

Gerar:

- produção energética (solar/eólica)
- impacto no consumo líquido
- comportamento mensal

## Fase 5 — Resultado e Cálculo de Custo

Calcular:

- consumo líquido (consumo - geração)
- custo horário (baseado na tarifa)
- agregações:
  - diário
  - mensal
  - por área

## Evolução do Produto (Visão futura)

Após o dataset base estar sólido:

**Fluxo do usuário final:**

- Usuário informa:
  - equipamentos que possui
- Sistema:
  - encontra equivalentes no dataset base
  - aplica perfis já existentes
- Resultado:
  - gera automaticamente um perfil energético personalizado

## Decisões arquiteturais implícitas

- Evitar lógica hardcoded → tudo deve vir da camada de configuração
- Fórmulas da planilha → virar funções determinísticas no backend
- Separação clara:
  - Configuração (imutável / administrável)
  - Instância (fazenda)
  - Simulação (derivada)

## Visão de backend

Um backend capaz de:

- Cadastrar e versionar datasets base
- Instanciar fazendas automaticamente
- Gerar consumo e geração por hora
- Calcular custo energético
- Servir como base para futuras interfaces (web/app)
