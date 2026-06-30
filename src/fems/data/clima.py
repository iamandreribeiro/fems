"""Carregador da base climática canônica (Base_Irradiacao da v8).

Lê o recurso empacotado `base_irradiacao_2025.json.gz` (stdlib gzip/json — sem
pandas/pyarrow) e o converte em `list[ClimaHora]`. Os timestamps são reconstruídos
para o ano pedido (2025 = 8760 h, não bissexto). A base é a referência validada;
um sintetizador para outros anos/regiões fica como evolução futura.
"""

from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta
from functools import lru_cache
from importlib.resources import files
from typing import Any

from fems.domain.simulation.types import ClimaHora

_RESOURCE = "base_irradiacao_2025.json.gz"


@lru_cache(maxsize=1)
def _raw() -> dict[str, Any]:
    data = files("fems.data").joinpath(_RESOURCE).read_bytes()
    parsed: dict[str, Any] = json.loads(gzip.decompress(data).decode("utf-8"))
    return parsed


def carregar_clima(ano: int = 2025) -> list[ClimaHora]:
    raw = _raw()
    n = int(raw["n"])
    ghi = raw["ghi"]
    temp = raw["temp"]
    vento = raw["vento"]
    fp = raw["fp"]
    base = datetime(ano, 1, 1)
    horas: list[ClimaHora] = []
    for i in range(n):
        dh = base + timedelta(hours=i)
        horas.append(
            ClimaHora(
                indice=i,
                data_hora=dh,
                mes=dh.month,
                hora=dh.hour,
                ghi=float(ghi[i]),
                temp=float(temp[i]),
                vento=float(vento[i]),
                fp=float(fp[i]),
            )
        )
    return horas
