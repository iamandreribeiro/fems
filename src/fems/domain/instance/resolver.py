"""Resolução de equipamentos: catálogo + porte + overrides -> lista efetiva.

Etapa pura que antecede o `Perfil_Area`. Para cada equipamento do catálogo, escolhe
a quantidade do porte (peq/med/grande) e aplica os overrides parciais (qtd/potência/
perfil) quando existirem. O resultado (`EquipamentoResolvido`, com `qtd` único) é o que
todo o resto do motor consome — assim o "cadastro personalizado" se propaga sozinho.
"""

from __future__ import annotations

from collections.abc import Sequence

from fems.domain.configuration.enums import Porte
from fems.domain.simulation.types import Equipamento, EquipamentoResolvido, OverrideSpec


def _qtd_do_porte(e: Equipamento, porte: Porte) -> float:
    if porte == Porte.PEQUENA:
        return e.qtd_peq
    if porte == Porte.MEDIA:
        return e.qtd_med
    return e.qtd_grande


def resolver_equipamentos(
    catalogo: Sequence[Equipamento],
    porte: Porte,
    overrides: Sequence[OverrideSpec] = (),
) -> list[EquipamentoResolvido]:
    ov_por_id = {o.equipamento_id: o for o in overrides}
    resolvidos: list[EquipamentoResolvido] = []
    for e in catalogo:
        qtd = _qtd_do_porte(e, porte)
        potencia = e.potencia_kw
        perfil = e.perfil
        ov = ov_por_id.get(e.id)
        if ov is not None:
            if ov.qtd is not None:
                qtd = ov.qtd
            if ov.potencia_kw is not None:
                potencia = ov.potencia_kw
            if ov.perfil is not None:
                perfil = ov.perfil
        resolvidos.append(
            EquipamentoResolvido(
                id=e.id,
                area=e.area,
                equipamento=e.equipamento,
                potencia_kw=potencia,
                qtd=qtd,
                perfil=perfil,
            )
        )
    return resolvidos
