from enum import StrEnum


class Area(StrEnum):
    """Áreas de carga de uma fazenda (espelha a coluna `Área` de Config_Equipamentos)."""

    ESCRITORIO = "escritorio"
    COZINHA = "cozinha"
    QUARTO = "quarto"
    IRRIGACAO = "irrigacao"


# Prefixo convencional do id de equipamento por área (ESC-01, COZ-01, QUA-01, IRR-01).
# Fonte de verdade única para a geração automática de id no cadastro.
AREA_PREFIXO: dict[Area, str] = {
    Area.ESCRITORIO: "ESC",
    Area.COZINHA: "COZ",
    Area.QUARTO: "QUA",
    Area.IRRIGACAO: "IRR",
}


class TipoGeracao(StrEnum):
    """Tipos de geração suportados (Config_Geracao)."""

    SOLAR_FV = "solar_fv"
    EOLICA = "eolica"


class Porte(StrEnum):
    """Porte da fazenda — seleciona Qtd_Peq / Qtd_Med / Qtd_Grande na instanciação."""

    PEQUENA = "Pequena"
    MEDIA = "Média"
    GRANDE = "Grande"


class TipoCarga(StrEnum):
    """Classe de uma carga instanciada (Cadastro_Cargas.Tipo)."""

    AGRICOLA = "Agrícola"
    SEDE = "Sede"
    ARMAZENAMENTO = "Armazenamento"


class StatusCarga(StrEnum):
    """Status de uma carga instanciada (ativa conforme flag de área + Cons_Max>0)."""

    ATIVO = "Ativo"
    INATIVO = "Inativo"


class TipoHorario(StrEnum):
    """Classificação tarifária horária (Tarifa Azul horossazonal)."""

    PONTA = "Ponta"
    FORA_PONTA = "Fora Ponta"
