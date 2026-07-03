"""Gera figuras PNG (matplotlib) dos 3 cenários, prontas para o artigo.

Lê o `dashboard_data.json` produzido por `scripts/gerar_cenarios.py` e escreve PNGs
em `<output>/figuras/`.

Run:  uv run python scripts/gerar_visuais.py --data out/cenarios/dashboard_data.json --output out
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _fig_custo_mensal(cenarios: list[dict], figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c in cenarios:
        custos = [m["custo_total_rs"] for m in c["mensal"]]
        ax.plot(MESES, custos, marker="o", label=f"{c['porte']} ({c['nome']})")
    ax.set_title("Custo mensal de energia por cenário")
    ax.set_ylabel("Custo (R$)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figdir / "custo_mensal.png", dpi=120)
    plt.close(fig)


def _fig_consumo_geracao(cenarios: list[dict], figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(cenarios))
    consumo = [c["totais"]["consumo_kwh"] for c in cenarios]
    geracao = [c["totais"]["geracao_kwh"] for c in cenarios]
    w = 0.38
    ax.bar([i - w / 2 for i in x], consumo, w, label="Consumo", color="#c0504d")
    ax.bar([i + w / 2 for i in x], geracao, w, label="Geração", color="#4f81bd")
    ax.set_xticks(list(x))
    ax.set_xticklabels([c["porte"] for c in cenarios])
    ax.set_title("Consumo x Geração anual por cenário")
    ax.set_ylabel("Energia (kWh/ano)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(figdir / "consumo_vs_geracao.png", dpi=120)
    plt.close(fig)


def _fig_perfil24(cenarios: list[dict], figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c in cenarios:
        horas = [p["hora"] for p in c["perfil24"]]
        consumo = [p["consumo_kwh"] for p in c["perfil24"]]
        ax.plot(horas, consumo, marker=".", label=f"{c['porte']}")
    ax.axvspan(18, 21, color="orange", alpha=0.15, label="Ponta (18h-21h)")
    ax.set_title("Perfil médio de consumo por hora do dia")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Consumo médio (kWh)")
    ax.set_xticks(range(0, 24, 2))
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(figdir / "perfil_24h.png", dpi=120)
    plt.close(fig)


def _fig_ranking(cenario: dict, area_key: str, titulo: str, fname: str, figdir: Path) -> None:
    itens = [i for i in cenario["ranking"].get(area_key, []) if i["kwh_ano"] > 0]
    if not itens:
        return
    itens = sorted(itens, key=lambda i: i["kwh_ano"])
    fig, ax = plt.subplots(figsize=(8, max(2.5, 0.5 * len(itens) + 1)))
    ax.barh([i["equipamento"] for i in itens], [i["kwh_ano"] for i in itens], color="#4f81bd")
    ax.set_title(titulo)
    ax.set_xlabel("kWh/ano")
    fig.tight_layout()
    fig.savefig(figdir / fname, dpi=120)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Figuras PNG dos cenários.")
    parser.add_argument("--data", required=True, type=Path, help="dashboard_data.json")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    cenarios = json.loads(args.data.read_text(encoding="utf-8"))["cenarios"]
    figdir = args.output / "figuras"
    figdir.mkdir(parents=True, exist_ok=True)

    _fig_custo_mensal(cenarios, figdir)
    _fig_consumo_geracao(cenarios, figdir)
    _fig_perfil24(cenarios, figdir)
    # Rankings da fazenda Média (representativa): residencial e agrícola.
    media = next((c for c in cenarios if c["porte"] == "Média"), cenarios[0])
    _fig_ranking(media, "escritorio", "Escritório (Média)", "ranking_escritorio.png", figdir)
    _fig_ranking(media, "cozinha", "Cozinha (Média)", "ranking_cozinha.png", figdir)
    _fig_ranking(media, "irrigacao", "Irrigação (Média)", "ranking_irrigacao.png", figdir)

    print(f"figuras em {figdir}")
    for p in sorted(figdir.glob("*.png")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
