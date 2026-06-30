"""Descarga da bateria — aplica o Cons_Min cheio em CADA hora de ponta.

Decisão de modelagem da planilha (não distribuído entre as horas de ponta): a cada
hora classificada como Ponta, a bateria injeta `descarga_kw` integralmente.
"""

from __future__ import annotations

from fems.domain.configuration.enums import TipoHorario


def descarga_bateria(tipo_horario: TipoHorario, descarga_kw: float) -> float:
    return descarga_kw if tipo_horario == TipoHorario.PONTA else 0.0
