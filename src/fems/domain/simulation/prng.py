"""Ruído estocástico determinístico — substitui `RANDBETWEEN(85,115)/100` da planilha.

Cada carga recebe sua própria sequência reprodutível derivada de (seed, ano, índice
da carga). Mesma fazenda + mesmo ano + mesma seed → exatamente a mesma série.
Não bate bit-a-bit com o RNG do Excel — por isso o consumo é validado por agregado,
não por valor horário (geração/bateria/custo são determinísticos e batem exato).
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

NOISE_LOW = 85
NOISE_HIGH = 115  # inclusivo


def noise_series(seed: int, ano: int, carga_idx: int, n: int) -> npt.NDArray[np.float64]:
    """n fatores de ruído em [0.85, 1.15], reprodutíveis por (seed, ano, carga_idx)."""
    ss = np.random.SeedSequence([seed, ano, carga_idx])
    rng = np.random.Generator(np.random.PCG64(ss))
    draws = rng.integers(NOISE_LOW, NOISE_HIGH + 1, size=n)
    return draws.astype(np.float64) / 100.0
