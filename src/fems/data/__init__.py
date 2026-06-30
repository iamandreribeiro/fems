"""Dados baseline empacotados (catálogo + clima) e seus carregadores.

- `catalog_seed`: literais tipados do catálogo (gerado de modelo_..._v8.xlsx).
- `clima`: carregador da base climática `base_irradiacao_2025.json.gz` (stdlib).
"""

from fems.data.clima import carregar_clima

__all__ = ["carregar_clima"]
