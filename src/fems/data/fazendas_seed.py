"""Fazendas de referência do projeto — semeadas numa base nova.

Espelham `tests/fixtures/faz_001.json` e `faz_002.json` (as fazendas-âncora citadas no
CLAUDE.md: Boa Vista e São Pedro). Semeadas de forma idempotente por
`scripts/seed_catalog.py` via `fems.services.seed.seed_fazendas`.
"""

from __future__ import annotations

from decimal import Decimal

from fems.domain.configuration.enums import Porte
from fems.domain.instance.fazenda import FazendaCreate

FAZENDAS_REFERENCIA: list[FazendaCreate] = [
    FazendaCreate(
        id="FAZ-001",
        nome="Fazenda Boa Vista",
        tamanho_ha=Decimal("80"),
        tipo=Porte.PEQUENA,
        id_solar="SOL-PEQ",
        id_eolica="EOL-PEQ",
        id_bateria="BAT-001",
    ),
    FazendaCreate(
        id="FAZ-002",
        nome="Fazenda São Pedro",
        tamanho_ha=Decimal("320"),
        tipo=Porte.MEDIA,
        id_solar="SOL-MED",
        id_eolica="EOL-MED",
        id_bateria="BAT-001",
    ),
]
