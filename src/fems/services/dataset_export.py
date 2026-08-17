"""Serializa resultados de simulação como bytes de Parquet, para download via API.

Espelha as tabelas escritas por `scripts/gerar_dataset.py`, mas em memória (sem tocar
o disco). Isolado num módulo próprio por depender de pandas/pyarrow (I/O binário).
"""

from __future__ import annotations

import dataclasses
import io

import pandas as pd

from fems.domain.simulation.types import FaturaHora


def fatura_parquet_bytes(fatura: list[FaturaHora]) -> bytes:
    """Série horária anual (aba `consumo_fatura`, 8.760 linhas) como um Parquet."""
    df = pd.DataFrame([dataclasses.asdict(f) for f in fatura])
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()
