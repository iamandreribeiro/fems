"""Gera o DATASET de uma fazenda (8.760 h) a partir de um arquivo de config.

Reusa o MESMO motor da API (`simular_fazenda`). Catálogo vem do módulo
`fems.data.catalog_seed` (não precisa de banco); clima da base empacotada.
Saída: Parquet (consumo_fatura + resumo_mensal). Opcional `--persist` grava o
cadastro + cargas no banco via FazendaService.

Config JSON = exatamente o payload de `POST /fazendas`, ex.:
  {"id": "FAZ-001", "nome": "Fazenda Boa Vista", "tamanho_ha": 80, "tipo": "Pequena",
   "tem_escritorio": true, "tem_cozinha": true, "tem_quarto": true, "tem_irrigacao": true,
   "id_solar": "SOL-PEQ", "id_eolica": "EOL-PEQ", "id_bateria": "BAT-001",
   "tarifa": "AZUL_HOROSSAZONAL", "seed": 20250101, "ano": 2025}

Run:
  uv run python scripts/gerar_dataset.py --config faz.json --output out/
  (ou: .venv/Scripts/python scripts/gerar_dataset.py --config faz.json --output out/)
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from pathlib import Path

import pandas as pd

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL
from fems.data.clima import carregar_clima
from fems.domain.configuration.enums import Porte
from fems.domain.simulation.engine import simular_fazenda
from fems.domain.simulation.types import FazendaSpec


def _spec_from_config(cfg: dict[str, object], ano_cli: int | None) -> FazendaSpec:
    porte = Porte(str(cfg["tipo"]))
    ano = ano_cli if ano_cli is not None else int(cfg.get("ano", 2025))  # type: ignore[arg-type]
    return FazendaSpec(
        id=str(cfg["id"]),
        nome=str(cfg["nome"]),
        tamanho_ha=float(cfg["tamanho_ha"]),  # type: ignore[arg-type]
        porte=porte,
        tem_escritorio=bool(cfg.get("tem_escritorio", True)),
        tem_cozinha=bool(cfg.get("tem_cozinha", True)),
        tem_quarto=bool(cfg.get("tem_quarto", True)),
        tem_irrigacao=bool(cfg.get("tem_irrigacao", True)),
        id_solar=cfg.get("id_solar"),  # type: ignore[arg-type]
        id_eolica=cfg.get("id_eolica"),  # type: ignore[arg-type]
        id_bateria=cfg.get("id_bateria"),  # type: ignore[arg-type]
        tarifa=str(cfg.get("tarifa", "AZUL_HOROSSAZONAL")),
        seed=int(cfg.get("seed", 20250101)),  # type: ignore[arg-type]
        ano=ano,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o dataset energético de uma fazenda.")
    parser.add_argument("--config", required=True, type=Path, help="JSON de cadastro da fazenda")
    parser.add_argument("--output", required=True, type=Path, help="diretório de saída")
    parser.add_argument("--year", type=int, default=None, help="ano da série (sobrepõe o config)")
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    spec = _spec_from_config(cfg, args.year)
    geradores = {g.id: g for g in GERADORES}
    clima = carregar_clima(spec.ano)

    result = simular_fazenda(spec, EQUIPAMENTOS, geradores, TARIFA_AZUL, clima)

    args.output.mkdir(parents=True, exist_ok=True)
    fatura_df = pd.DataFrame([dataclasses.asdict(f) for f in result.fatura])
    resumo_df = pd.DataFrame([dataclasses.asdict(r) for r in result.resumo])
    cargas_df = pd.DataFrame([dataclasses.asdict(c) for c in result.cargas])

    fatura_path = args.output / "consumo_fatura.parquet"
    resumo_path = args.output / "resumo_mensal.parquet"
    cargas_path = args.output / "cadastro_cargas.parquet"
    fatura_df.to_parquet(fatura_path, index=False)
    resumo_df.to_parquet(resumo_path, index=False)
    cargas_df.to_parquet(cargas_path, index=False)

    print(f"[{spec.id}] {spec.nome} — ano {spec.ano}, seed {spec.seed}")
    print(f"  {fatura_path}  ({len(fatura_df)} linhas)")
    print(f"  {resumo_path}  ({len(resumo_df)} meses)")
    print(f"  {cargas_path}  ({len(cargas_df)} cargas)")
    consumo = float(fatura_df["consumo_kwh"].sum())
    geracao = float(fatura_df["geracao_kwh"].sum())
    custo = float(fatura_df["custo_rs"].sum())
    print(f"  ano: consumo={consumo:.1f} kWh | geracao={geracao:.1f} kWh | custo=R$ {custo:.2f}")


if __name__ == "__main__":
    main()
