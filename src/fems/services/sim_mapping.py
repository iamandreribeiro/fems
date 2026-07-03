"""Conversores ORM → tipos puros do motor (fronteira service ↔ domínio).

O motor (`domain.simulation`) só conhece dataclasses puras em float. Aqui traduzimos
as linhas do banco (Decimal/ENUM) para esses tipos antes de simular.
"""

from __future__ import annotations

from decimal import Decimal

from fems.domain.instance.override import OverrideEquipamentoCreate
from fems.domain.simulation.types import (
    CargaInstanciada,
    Equipamento,
    FazendaSpec,
    Gerador,
    OverrideSpec,
    TarifaHora,
)
from fems.repositories.models import (
    ConfiguracaoGeracaoORM,
    EquipamentoORM,
    FazendaCargaORM,
    FazendaORM,
    FazendaOverrideORM,
    TarifaHoraORM,
)


def equipamento_from_orm(o: EquipamentoORM) -> Equipamento:
    return Equipamento(
        id=o.id,
        area=o.area,
        equipamento=o.equipamento,
        potencia_kw=float(o.potencia_kw),
        qtd_peq=float(o.qtd_peq),
        qtd_med=float(o.qtd_med),
        qtd_grande=float(o.qtd_grande),
        perfil=tuple(float(x) for x in o.perfil_horario),
    )


def gerador_from_orm(o: ConfiguracaoGeracaoORM) -> Gerador:
    return Gerador(
        id=o.id,
        tipo=o.tipo,
        pot_nominal_kwp=float(o.pot_nominal_kwp),
        eficiencia_pct=float(o.eficiencia_pct),
        ref_conversao=float(o.ref_conversao),
        gen_max_kw=float(o.gen_max_kw),
        gen_min_kw=float(o.gen_min_kw),
    )


def tarifa_hora_from_orm(o: TarifaHoraORM) -> TarifaHora:
    return TarifaHora(hora=o.hora, preco_kwh=float(o.preco_kwh), tipo=o.tipo)


def fazenda_spec_from_orm(o: FazendaORM) -> FazendaSpec:
    return FazendaSpec(
        id=o.id,
        nome=o.nome,
        tamanho_ha=float(o.tamanho_ha),
        porte=o.tipo,
        tem_escritorio=o.tem_escritorio,
        tem_cozinha=o.tem_cozinha,
        tem_quarto=o.tem_quarto,
        tem_irrigacao=o.tem_irrigacao,
        id_solar=o.id_solar,
        id_eolica=o.id_eolica,
        id_bateria=o.id_bateria,
        tarifa=o.tarifa,
        seed=o.seed,
        ano=o.ano,
    )


def _perfil_tuple(v: list[float] | None) -> tuple[float, ...] | None:
    return None if v is None else tuple(float(x) for x in v)


def override_spec_from_orm(o: FazendaOverrideORM) -> OverrideSpec:
    return OverrideSpec(
        equipamento_id=o.equipamento_id,
        qtd=None if o.qtd is None else float(o.qtd),
        potencia_kw=None if o.potencia_kw is None else float(o.potencia_kw),
        perfil=_perfil_tuple(o.perfil_horario),
    )


def override_spec_from_create(ov: OverrideEquipamentoCreate) -> OverrideSpec:
    return OverrideSpec(
        equipamento_id=ov.equipamento_id,
        qtd=None if ov.qtd is None else float(ov.qtd),
        potencia_kw=None if ov.potencia_kw is None else float(ov.potencia_kw),
        perfil=_perfil_tuple(ov.perfil_horario),
    )


def override_orm_from_create(fazenda_id: str, ov: OverrideEquipamentoCreate) -> FazendaOverrideORM:
    return FazendaOverrideORM(
        fazenda_id=fazenda_id,
        equipamento_id=ov.equipamento_id,
        qtd=ov.qtd,
        potencia_kw=ov.potencia_kw,
        perfil_horario=ov.perfil_horario,
    )


def carga_orm_from_instanciada(fazenda_id: str, c: CargaInstanciada) -> FazendaCargaORM:
    # Arredonda à escala da coluna (Numeric(12,6)) — remove ruído de float (ex.: 0.354).
    return FazendaCargaORM(
        fazenda_id=fazenda_id,
        carga=c.carga,
        tipo=c.tipo,
        cons_max_kw=Decimal(str(round(c.cons_max_kw, 6))),
        cons_min_kw=Decimal(str(round(c.cons_min_kw, 6))),
        status=c.status,
    )
