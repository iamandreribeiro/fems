"""Instanciação automática de cargas por fazenda (Cadastro_Cargas).

A partir do catálogo + porte + flags de área, deriva as 7 cargas + a bateria,
exatamente como a planilha v8.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from fems.domain.configuration.enums import StatusCarga, TipoCarga
from fems.domain.instance.perfil_area import LoadDef, perfis_por_carga
from fems.domain.instance.resolver import resolver_equipamentos
from fems.domain.simulation.types import CargaInstanciada, Equipamento, FazendaSpec, OverrideSpec

# Quirk fiel à planilha: o Cons_Max é o MAX de APENAS três colunas do Perfil_Area —
# 00h, 01h e 11h (células C, D e N da fórmula `=MAX(SUMPRODUCT(...C...), (...D...),
# (...N...))`). NÃO é o pico das 24h. Reproduzir exatamente (CLAUDE.md, princípio 2).
CONS_MAX_HOURS: tuple[int, int, int] = (0, 1, 11)

CONS_MIN_FATOR = 0.3
BATERIA_FATOR_CAPACIDADE = 0.66
BATERIA_FATOR_DESCARGA = 0.175


def cons_max_from_perfil(perfil: tuple[float, ...]) -> float:
    return max(perfil[h] for h in CONS_MAX_HOURS)


def _excel_round(x: float) -> int:
    """ROUND(x, 0) do Excel — meio para cima (away-from-zero); x sempre ≥ 0 aqui."""
    return math.floor(x + 0.5)


def capacidade_bateria(soma_cons_max: float) -> float:
    """ROUND(soma * 0.66 / 5, 0) * 5 — capacidade arredondada ao múltiplo de 5."""
    return float(_excel_round(soma_cons_max * BATERIA_FATOR_CAPACIDADE / 5) * 5)


def cargas_from_perfis(
    fazenda: FazendaSpec, perfis: Sequence[tuple[LoadDef, tuple[float, ...]]]
) -> list[CargaInstanciada]:
    """Deriva as cargas instanciadas a partir dos perfis já computados (+ bateria)."""
    cargas: list[CargaInstanciada] = []
    soma_cons_max = 0.0
    for load, perfil in perfis:
        cons_max = cons_max_from_perfil(perfil)
        cons_min = cons_max * CONS_MIN_FATOR
        ativa = bool(getattr(fazenda, load.flag))
        status = StatusCarga.ATIVO if (cons_max > 0.0 and ativa) else StatusCarga.INATIVO
        cargas.append(CargaInstanciada(load.carga, load.tipo, cons_max, cons_min, status))
        soma_cons_max += cons_max

    if fazenda.id_bateria is not None:
        cap = capacidade_bateria(soma_cons_max)
        cargas.append(
            CargaInstanciada(
                carga="Bateria",
                tipo=TipoCarga.ARMAZENAMENTO,
                cons_max_kw=cap,
                cons_min_kw=cap * BATERIA_FATOR_DESCARGA,
                status=StatusCarga.ATIVO,
            )
        )
    return cargas


def instanciar_cargas(
    fazenda: FazendaSpec,
    equipamentos: Sequence[Equipamento],
    overrides: Sequence[OverrideSpec] = (),
) -> list[CargaInstanciada]:
    """Atalho: resolve (porte + overrides), computa os perfis e deriva as cargas (+ bateria)."""
    resolvidos = resolver_equipamentos(equipamentos, fazenda.porte, overrides)
    perfis = perfis_por_carga(resolvidos)
    return cargas_from_perfis(fazenda, perfis)
