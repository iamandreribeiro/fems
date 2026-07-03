"""Roda os 3 cenários de porte (Pequena/Média/Grande) e agrega os dados para a
apresentação visual.

Saída: `<output>/dashboard_data.json` (totais, resumo mensal, perfil médio 24h e
ranking por área de cada cenário) + os Parquets de cada cenário. Reusa o mesmo motor
`simular_fazenda`; não precisa de banco.

Run:  uv run python scripts/gerar_cenarios.py --output out/cenarios
      (ou: .venv/Scripts/python scripts/gerar_cenarios.py --output out/cenarios)
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

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
CENARIOS = ["faz_001", "faz_002", "faz_003"]  # Pequena / Média / Grande


def _spec(cfg: dict) -> FazendaSpec:
    return FazendaSpec(
        id=str(cfg["id"]),
        nome=str(cfg["nome"]),
        tamanho_ha=float(cfg["tamanho_ha"]),
        porte=Porte(str(cfg["tipo"])),
        tem_escritorio=bool(cfg.get("tem_escritorio", True)),
        tem_cozinha=bool(cfg.get("tem_cozinha", True)),
        tem_quarto=bool(cfg.get("tem_quarto", True)),
        tem_irrigacao=bool(cfg.get("tem_irrigacao", True)),
        id_solar=cfg.get("id_solar"),
        id_eolica=cfg.get("id_eolica"),
        id_bateria=cfg.get("id_bateria"),
        tarifa=str(cfg.get("tarifa", "AZUL_HOROSSAZONAL")),
        seed=int(cfg.get("seed", 20250101)),
        ano=int(cfg.get("ano", 2025)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera os 3 cenários + dados do dashboard.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    geradores = {g.id: g for g in GERADORES}
    clima = carregar_clima(2025)

    cenarios = []
    for nome_fix in CENARIOS:
        cfg = json.loads((FIXTURES / f"{nome_fix}.json").read_text(encoding="utf-8"))
        spec = _spec(cfg)
        res = simular_fazenda(spec, EQUIPAMENTOS, geradores, TARIFA_AZUL, clima)

        fatura = pd.DataFrame([dataclasses.asdict(f) for f in res.fatura])
        fatura.to_parquet(args.output / f"{spec.id}_consumo_fatura.parquet", index=False)

        perfil24 = fatura.groupby("hora")[["consumo_kwh", "geracao_kwh"]].mean().reset_index()
        ranking = {
            area.value: [dataclasses.asdict(i) | {"area": area.value} for i in itens]
            for area, itens in res.ranking.items()
        }
        cenarios.append(
            {
                "id": spec.id,
                "nome": spec.nome,
                "porte": spec.porte.value,
                "tamanho_ha": spec.tamanho_ha,
                "totais": {
                    "consumo_kwh": float(fatura["consumo_kwh"].sum()),
                    "geracao_kwh": float(fatura["geracao_kwh"].sum()),
                    "custo_rs": float(fatura["custo_rs"].sum()),
                    "bateria_kwh": float(fatura["bateria_descarga_kwh"].sum()),
                },
                "mensal": [dataclasses.asdict(r) for r in res.resumo],
                "perfil24": perfil24.to_dict(orient="records"),
                "ranking": ranking,
            }
        )

    out_json = args.output / "dashboard_data.json"
    out_json.write_text(json.dumps({"cenarios": cenarios}, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_json}")
    for c in cenarios:
        t = c["totais"]
        print(
            f"  {c['porte']:8s} {c['nome']}: consumo={t['consumo_kwh']:.0f} kWh | "
            f"geracao={t['geracao_kwh']:.0f} kWh | custo=R$ {t['custo_rs']:.0f}"
        )


if __name__ == "__main__":
    main()
