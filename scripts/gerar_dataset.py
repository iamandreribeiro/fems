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
import asyncio
import dataclasses
import json
from pathlib import Path

import pandas as pd

from fems.data.catalog_seed import EQUIPAMENTOS, GERADORES, TARIFA_AZUL
from fems.data.clima import carregar_clima
from fems.domain.configuration.enums import Porte
from fems.domain.simulation.engine import simular_fazenda
from fems.domain.simulation.types import (
    Equipamento,
    FazendaSpec,
    Gerador,
    OverrideSpec,
    SimResult,
    TarifaHora,
)

Catalogo = tuple[list[Equipamento], list[Gerador], list[TarifaHora]]


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


def _overrides_from_config(cfg: dict[str, object]) -> list[OverrideSpec]:
    raw = cfg.get("overrides") or []
    specs: list[OverrideSpec] = []
    for o in raw:  # type: ignore[union-attr]
        perfil = o.get("perfil_horario")
        specs.append(
            OverrideSpec(
                equipamento_id=str(o["equipamento_id"]),
                qtd=o.get("qtd"),
                potencia_kw=o.get("potencia_kw"),
                perfil=tuple(float(x) for x in perfil) if perfil else None,
            )
        )
    return specs


async def _catalogo_do_banco(tarifa_nome: str) -> Catalogo:
    """Carrega o catálogo do Postgres (mesmos conversores ORM→motor da API).

    Import lazy: só toca em core.database/settings quando --from-db é usado, mantendo
    o caminho padrão (módulo) 100% offline.
    """
    from fems.core.database import SessionLocal
    from fems.repositories.equipamento_repository import EquipamentoRepository
    from fems.repositories.geracao_repository import ConfiguracaoGeracaoRepository
    from fems.repositories.tarifa_repository import TarifaRepository
    from fems.services.sim_mapping import (
        equipamento_from_orm,
        gerador_from_orm,
        tarifa_hora_from_orm,
    )

    async with SessionLocal() as s:
        equipamentos = [equipamento_from_orm(o) for o in await EquipamentoRepository(s).list()]
        geradores = [gerador_from_orm(o) for o in await ConfiguracaoGeracaoRepository(s).list()]
        tar_orm = await TarifaRepository(s).get_by_nome(tarifa_nome)
    if not equipamentos:
        raise SystemExit("erro: catálogo vazio no banco — rode scripts/seed_catalog.py")
    if tar_orm is None:
        raise SystemExit(f"erro: tarifa '{tarifa_nome}' não cadastrada no banco")
    tarifa = [tarifa_hora_from_orm(h) for h in tar_orm.horas]
    return equipamentos, geradores, tarifa


def _validar_overrides(overrides: list[OverrideSpec], equipamentos: list[Equipamento]) -> None:
    ids = {e.id for e in equipamentos}
    desconhecidos = sorted({o.equipamento_id for o in overrides if o.equipamento_id not in ids})
    if desconhecidos:
        raise SystemExit(
            "erro: override referencia equipamento(s) fora do catálogo: " + ", ".join(desconhecidos)
        )


def _escrever_base_completa(result: SimResult, output: Path) -> None:
    """Grava as abas Equipamentos, Consumo (por carga) e Geração (por gerador)."""
    kwh_por_eq = {
        item.equipamento_id: (item.kwh_ano, item.custo_ano)
        for itens in result.ranking.values()
        for item in itens
    }
    equipamentos_df = pd.DataFrame(
        [
            {
                "equipamento_id": e.id,
                "area": e.area.value,
                "equipamento": e.equipamento,
                "potencia_kw": e.potencia_kw,
                "qtd": e.qtd,
                "perfil_horario": list(e.perfil),
                "kwh_ano": kwh_por_eq.get(e.id, (0.0, 0.0))[0],
                "custo_ano": kwh_por_eq.get(e.id, (0.0, 0.0))[1],
            }
            for e in result.equipamentos
        ]
    )
    consumo_df = pd.DataFrame([dataclasses.asdict(c) for c in result.cargas_horarias])
    geracao_df = pd.DataFrame([dataclasses.asdict(g) for g in result.geracao_horaria])
    for df in (consumo_df, geracao_df):
        if "tipo" in df.columns:
            df["tipo"] = df["tipo"].astype(str)

    equipamentos_df.to_parquet(output / "equipamentos.parquet", index=False)
    consumo_df.to_parquet(output / "consumo.parquet", index=False)
    geracao_df.to_parquet(output / "geracao.parquet", index=False)
    print(f"  {output / 'equipamentos.parquet'}  ({len(equipamentos_df)} equipamentos)")
    print(f"  {output / 'consumo.parquet'}  ({len(consumo_df)} linhas — aba Cargas)")
    print(f"  {output / 'geracao.parquet'}  ({len(geracao_df)} linhas — aba Geração)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o dataset energético de uma fazenda.")
    parser.add_argument("--config", required=True, type=Path, help="JSON de cadastro da fazenda")
    parser.add_argument("--output", required=True, type=Path, help="diretório de saída")
    parser.add_argument("--year", type=int, default=None, help="ano da série (sobrepõe o config)")
    parser.add_argument(
        "--completo",
        action="store_true",
        help="também grava as abas equipamentos, consumo (por carga) e geração (por gerador)",
    )
    parser.add_argument(
        "--from-db",
        action="store_true",
        help="carrega o catálogo do Postgres (reflete edições via API) em vez do módulo empacotado",
    )
    args = parser.parse_args()

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    spec = _spec_from_config(cfg, args.year)
    overrides = _overrides_from_config(cfg)

    if args.from_db:
        equipamentos, geradores_lst, tarifa = asyncio.run(_catalogo_do_banco(spec.tarifa))
        fonte = "banco"
    else:
        equipamentos, geradores_lst, tarifa = list(EQUIPAMENTOS), list(GERADORES), list(TARIFA_AZUL)
        fonte = "módulo (catalog_seed)"

    _validar_overrides(overrides, equipamentos)
    geradores = {g.id: g for g in geradores_lst}
    clima = carregar_clima(spec.ano)

    result = simular_fazenda(
        spec, equipamentos, geradores, tarifa, clima, overrides, detalhado=args.completo
    )

    args.output.mkdir(parents=True, exist_ok=True)
    fatura_df = pd.DataFrame([dataclasses.asdict(f) for f in result.fatura])
    resumo_df = pd.DataFrame([dataclasses.asdict(r) for r in result.resumo])
    cargas_df = pd.DataFrame([dataclasses.asdict(c) for c in result.cargas])
    ranking_df = pd.DataFrame(
        [dataclasses.asdict(item) for itens in result.ranking.values() for item in itens]
    )

    fatura_path = args.output / "consumo_fatura.parquet"
    resumo_path = args.output / "resumo_mensal.parquet"
    cargas_path = args.output / "cadastro_cargas.parquet"
    ranking_path = args.output / "ranking_equipamentos.parquet"
    fatura_df.to_parquet(fatura_path, index=False)
    resumo_df.to_parquet(resumo_path, index=False)
    cargas_df.to_parquet(cargas_path, index=False)
    ranking_df.to_parquet(ranking_path, index=False)

    print(f"[{spec.id}] {spec.nome} — ano {spec.ano}, seed {spec.seed} — catálogo: {fonte}")
    print(f"  {fatura_path}  ({len(fatura_df)} linhas)")
    print(f"  {resumo_path}  ({len(resumo_df)} meses)")
    print(f"  {cargas_path}  ({len(cargas_df)} cargas)")
    print(f"  {ranking_path}  ({len(ranking_df)} equipamentos)")
    if args.completo:
        _escrever_base_completa(result, args.output)
    consumo = float(fatura_df["consumo_kwh"].sum())
    geracao = float(fatura_df["geracao_kwh"].sum())
    custo = float(fatura_df["custo_rs"].sum())
    print(f"  ano: consumo={consumo:.1f} kWh | geracao={geracao:.1f} kWh | custo=R$ {custo:.2f}")


if __name__ == "__main__":
    main()
