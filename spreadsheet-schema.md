# Modelo de Simulação Energética — Estrutura da Planilha (v8)

> Documentação da estrutura de `modelo_gestao_energia_fazenda_v8.xlsx`.
> Este documento é a **fonte de verdade** que orienta o schema do banco de dados
> e as regras de negócio do backend. Cada aba é uma camada; a lógica de fórmula
> de cada coluna deve virar uma função determinística no software.

## Visão geral das camadas

A planilha tem 11 abas organizadas em quatro camadas:

| Camada | Abas | Papel |
|---|---|---|
| **Configuração** (imutável/administrável) | `Config_Equipamentos`, `Perfil_Area`, `Config_Geracao`, `Tarifa` | Baseline: equipamentos padrão, perfis horários derivados, parâmetros de geração e tarifa |
| **Cadastro** (instância) | `Cadastro_Fazenda`, `Cadastro_Cargas` | Registro de fazendas e instanciação automática de cargas por fazenda |
| **Simulação** (derivada) | `Base_Irradiacao`, `Geracao`, `Cargas` | Série temporal horária: clima, geração e consumo |
| **Resultados** (derivada) | `Consumo_Fatura`, `Resumo_Mensal` | Saldo líquido, custo por hora e agregações mensais |

O princípio paramétrico central: **uma nova fazenda exige apenas uma nova linha em
`Cadastro_Fazenda`**; todas as demais relações se propagam por fórmula.

---

## Camada de Configuração

### `Config_Equipamentos` (20 equipamentos, linhas 2–21)

Catálogo de cargas padrão. Uma linha por equipamento.

Colunas: `ID`, `Área`, `Equipamento`, `Potência_kW`, `Qtd_Peq`, `Qtd_Med`, e
**24 colunas horárias** `00h`…`23h` (fatores de uso normalizados 0–1 por hora).

- **Áreas:** Escritório (ESC-01..06), Cozinha (COZ-01..06), Quarto (QUA-01..04),
  Irrigação/Lavoura (IRR-01..).
- `Qtd_Peq` / `Qtd_Med`: quantidade padrão do equipamento por porte de fazenda
  (pequena / média).
- As 24 colunas horárias são o **perfil de uso** (fração da potência ligada naquela hora).
- Equipamentos-chave de irrigação: **Pivô central = 4.0 kW**, e categorias
  identificadas pelo nome em `Equipamento` (Pivô central, Bomba auxiliar,
  Secadora/Silo, Quadro de automação) — usadas como filtro em `Perfil_Area`.

### `Perfil_Area` (linhas 3–16) — DERIVADO

Potência por carga × hora, agregada a partir de `Config_Equipamentos`.
Uma linha por combinação **(Carga, Tipo_Fazenda)**.

Colunas: `Carga`, `Tipo_Fazenda` (Pequena/Média), 24 colunas `00h_kW`…`23h_kW`,
`Total_kWh/dia`.

Cargas modeladas: Escritório, Cozinha, Quarto, Pivô, Bomba_Aux, Secadora,
Quadro_Auto (cada uma em Pequena e Média).

Fórmula de cada célula horária (padrão SUMPRODUCT):

```
=SUMPRODUCT(
   (Config_Equipamentos!$B$2:$B$21 = "<Área>")
   * Config_Equipamentos!$D$2:$D$21        // Potência_kW
   * Config_Equipamentos!$<QtdCol>$2:$21   // Qtd_Peq (E) p/ Pequena, Qtd_Med (F) p/ Média
   * Config_Equipamentos!$<HoraCol>$2:$21  // fator horário
)
```

As cargas agrícolas adicionam um segundo filtro pelo nome do equipamento, ex.:
`(Config_Equipamentos!$C$2:$C$21="Pivô central")`. `Total_kWh/dia = SUM(C:Z)`.

→ **No backend:** isto é uma agregação `GROUP BY (area, tipo_fazenda, hora)` com
soma de `potencia * qtd * fator_hora`. Não hardcodar — derivar do catálogo.

### `Config_Geracao` (linhas 2–5)

Parâmetros dos geradores. Uma linha por gerador-padrão.

Colunas: `ID`, `Tipo`, `Pot_Nominal_kWp`, `Eficiência_%`, `Ref_Conversão`,
`Gen_Max_kW`, `Gen_Min_kW`, `Observação`.

| ID | Tipo | kWp | Efic.% | Ref_Conversão | Max | Min |
|---|---|---|---|---|---|---|
| SOL-PEQ | Solar FV | 10 | 85 | 1100 (GHI ref W/m²) | 10 | 0.5 |
| SOL-MED | Solar FV | 40 | 87 | 1100 | 40 | 3.0 |
| EOL-PEQ | Eólica | 3 | 85 | 10 (vento ref m/s) | 3 | 0.1 |
| EOL-MED | Eólica | 10 | 87 | 10 | 10 | 0.3 |

**Princípio importante (lição aprendida):** a geração eólica segue a **mesma
estrutura normalizada** da solar — velocidade do vento ÷ vento de referência,
× capacidade, com clamp min/max. **Não** se usa curva cúbica genérica de
potência eólica. Espelhar a metodologia da referência, não substituir por
fórmula de domínio genérica.

### `Tarifa` (24 linhas horárias, 2–25)

Tarifa Azul horossazonal. Colunas: `Hora`, `Energia_R$/kWh`, `Tipo`.

- **Fora Ponta:** R$ 0,6813 /kWh
- **Ponta:** R$ 1,1039 /kWh — **horas 18:00, 19:00, 20:00** (Tipo = "Ponta")

---

## Camada de Cadastro

### `Cadastro_Fazenda` (linhas 2–3) — fonte de verdade paramétrica

Uma linha por fazenda. Adicionar fazenda = adicionar linha aqui.

Colunas: `ID_Fazenda`, `Nome`, `Tamanho_ha`, `Tipo` (Pequena/Média),
`Tem_Escritório`, `Tem_Cozinha`, `Tem_Quarto`, `Tem_Irrigação` (flags 0/1),
`ID_Solar`, `ID_Eólica`, `ID_Bateria`.

| ID | Nome | ha | Tipo | Solar | Eólica | Bateria |
|---|---|---|---|---|---|---|
| FAZ-001 | Fazenda Boa Vista | 80 | Pequena | SOL-PEQ | EOL-PEQ | BAT-001 |
| FAZ-002 | Fazenda São Pedro | 320 | Média | SOL-MED | EOL-MED | BAT-001 |

### `Cadastro_Cargas` (linhas 2–17) — instanciação automática

Uma linha por (fazenda × carga). As 7 cargas por fazenda + 1 linha de bateria.

Colunas: `ID_Fazenda`, `Nome_Fazenda`, `Carga`, `Tipo`, `Cons_Max_kW`,
`Cons_Min_kW`, `Status`.

- `ID_Fazenda`/`Nome_Fazenda`: referência direta a `Cadastro_Fazenda`.
- `Cons_Max_kW`: pico da carga, via `MAX` de SUMPRODUCTs sobre `Perfil_Area`,
  selecionando o porte pelo `Tipo` da fazenda.
- `Cons_Min_kW = Cons_Max * 0.3` (exceto bateria, ver abaixo).
- `Status`: `IF(Cons_Max=0,"Inativo", IF(flag_area=1,"Ativo","Inativo"))` —
  a flag usada depende da carga (Tem_Irrigação para agrícolas, Tem_Escritório
  para Escritório, etc.).

**Bateria como carga padrão** (decisão de modelagem deliberada — mantém o modelo
consistente e extensível, sem aba dedicada):

- Tipo = `Armazenamento`, nome = `Bateria`, Status = `Ativo`.
- `Cons_Max` (capacidade) = `ROUND(SUM(Cons_Max das cargas da fazenda) * 0.66 / 5, 0) * 5`
  (arredondado ao múltiplo de 5).
- `Cons_Min` (fator de descarga) = `Cons_Max * 0.175`.

---

## Camada de Simulação (série temporal horária, ano 2025)

### `Base_Irradiacao` (8.760 linhas — ano completo)

Base climática sintética horária. Colunas: `Data_Hora`, `Mês`, `Hora`,
`GHI_W/m²`, `Temp_°C`, `Vento_m/s`, `FP` (fator de planta/disponibilidade),
`Vento_Normalizado`.

- `Vento_Normalizado = MIN(1, Vento_m/s / Vento_Ref) * FP`, onde `Vento_Ref`
  vem de `Config_Geracao!$E$4` (10 m/s). Espelha a normalização do GHI usada na
  geração solar.

### `Geracao` (formato longo)

Uma linha por **fazenda × gerador × hora**. Colunas: `Data_Hora`, `Hora`,
`ID_Fazenda`, `ID_Gerador`, `Tipo`, `Energia_Gerada_kWh` (coluna única).

Geradores por ID: SOL-PEQ, SOL-MED, EOL-PEQ, EOL-MED.

Fórmula solar (normalizada, com clamp e cutoff mínimo):

```
Energia = MIN(Gen_Max,
              IF( (GHI/Ref) * FP * kWp * (Efic/100) < Gen_Min, 0,
                  MAX(Gen_Min, (GHI/Ref) * FP * kWp * (Efic/100)) ))
```

Fórmula eólica (mesma estrutura, usando `Vento_Normalizado` no lugar de `GHI/Ref*FP`):

```
Energia = MIN(Gen_Max,
              IF( Vento_Norm * kWp * (Efic/100) < Gen_Min, 0,
                  MAX(Gen_Min, Vento_Norm * kWp * (Efic/100)) ))
```

### `Cargas` (formato longo)

Uma linha por **fazenda × carga × hora**. Colunas: `Data_Hora`, `Hora`,
`ID_Fazenda`, `Carga`, `Tipo`, `Consumo_kWh`.

Fórmula de consumo (perfil horário com variação estocástica ±15%):

```
Consumo = IF(Cons_Max=0, 0,
           IF(perfil_hora=0, 0,
              MIN(Cons_Max, MAX(Cons_Min, perfil_hora * RANDBETWEEN(85,115)/100))))
```

`perfil_hora` vem da célula horária correspondente em `Perfil_Area`.

→ **No backend:** o `RANDBETWEEN(85,115)/100` é o ruído sintético. Substituir por
um gerador pseudoaleatório com seed para reprodutibilidade.

---

## Camada de Resultados

### `Consumo_Fatura` (formato longo, por fazenda × hora)

Colunas: `ID_Fazenda`, `Data_Hora`, `Hora`, `Consumo_kWh`, `Geração_kWh`,
`Saldo_Rede_kWh`, `Tarifa_R$`, `Custo_R$`, `Tipo_Horário`,
`Bateria_Descarga_kWh`, `Saldo_Liquido_kWh`.

- `Consumo_kWh = SUM` das linhas de `Cargas` daquela fazenda/hora.
- `Geração_kWh = soma` das linhas de `Geracao` (solar + eólica) daquela fazenda/hora.
- `Saldo_Rede = Consumo - Geração`.
- `Tipo_Horário`/`Tarifa_R$`: lookup em `Tarifa` pela hora.
- **`Bateria_Descarga_kWh = IF(Tipo_Horário="Ponta", Cons_Min_bateria, 0)`** —
  a descarga aplica o **valor cheio de `Cons_Min` em CADA hora de ponta**, não
  dividido entre as horas de ponta. (Ex.: bateria de 40 kWh descarrega a 7 kW;
  os 7 kW valem para cada hora de ponta individualmente.)
- `Saldo_Liquido_kWh = MAX(0, Consumo - Geração - Bateria_Descarga)`.
- `Custo_R$ = Saldo_Liquido * Tarifa`.

### `Resumo_Mensal`

Uma linha por fazenda. Agrega `Consumo_Fatura` por faixas de linha.

Colunas: `Fazenda`, `Consumo_kWh`, `Geração_kWh`, `Saldo_Rede_kWh`,
`Custo_Total_R$`, `Custo_Ponta_R$`, `Custo_Fora_Ponta_R$`,
`Bateria_Descarga_kWh`, `Saldo_Liquido_kWh`.

- `Custo_Ponta = SUMPRODUCT((Tipo_Horário="Ponta") * Custo_R$)`.

---

## Observações para a migração ao backend

1. **Escopo temporal atual:** `Base_Irradiacao` cobre o ano inteiro (8.760 h),
   mas as abas a jusante (`Geracao`, `Cargas`, `Consumo_Fatura`) estão populadas
   apenas para **~janeiro (1 mês)** nesta v8. Ao migrar, o backend deve gerar a
   série completa de 8.760 h para todas as fazendas.
2. **Fórmulas → funções determinísticas.** Cada coluna calculada acima vira uma
   função pura. O `RANDBETWEEN` deve usar seed.
3. **Separação de camadas no software:** Configuração (versionável/imutável) →
   Instância (fazenda) → Simulação (derivada) → Resultados (derivada).
4. **Geração eólica = mesma estrutura normalizada da solar.** Não introduzir
   curva cúbica genérica.
5. **Bateria é uma carga (`Armazenamento`)**, não uma entidade especial.
