from enum import StrEnum


class Area(StrEnum):
    """Áreas de carga de uma fazenda (espelha a coluna `Área` de Config_Equipamentos)."""

    ESCRITORIO = "escritorio"
    COZINHA = "cozinha"
    QUARTO = "quarto"
    IRRIGACAO = "irrigacao"


class TipoGeracao(StrEnum):
    """Tipos de geração suportados (Config_Geracao)."""

    SOLAR_FV = "solar_fv"
    EOLICA = "eolica"


class Porte(StrEnum):
    """Porte da fazenda — seleciona Qtd_Peq vs Qtd_Med na instanciação."""

    PEQUENA = "Pequena"
    MEDIA = "Média"


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
