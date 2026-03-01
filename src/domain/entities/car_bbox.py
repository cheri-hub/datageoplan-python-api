"""
Entidades de domínio para consulta de CARs por Bounding Box.

Enums para UF, status e tipo de imóvel rural no SICAR.
"""

from enum import Enum


class UfSicar(str, Enum):
    """Siglas das Unidades Federativas brasileiras."""

    AC = "AC"
    AL = "AL"
    AM = "AM"
    AP = "AP"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MG = "MG"
    MS = "MS"
    MT = "MT"
    PA = "PA"
    PB = "PB"
    PE = "PE"
    PI = "PI"
    PR = "PR"
    RJ = "RJ"
    RN = "RN"
    RO = "RO"
    RR = "RR"
    RS = "RS"
    SC = "SC"
    SE = "SE"
    SP = "SP"
    TO = "TO"


class StatusImovelSicar(str, Enum):
    """Status de cadastro de imóvel no SICAR."""

    ATIVO = "AT"
    PENDENTE = "PE"
    CANCELADO = "CA"
    INSCRITO = "IN"
    RETIFICADO = "RE"
    SUSPENSO = "SU"


class TipoImovelSicar(str, Enum):
    """Tipo de imóvel rural no SICAR."""

    IMOVEL_RURAL = "IRU"
    POVOS_COMUNIDADES_TRADICIONAIS = "PCT"
    ASSENTAMENTO_REFORMA_AGRARIA = "AST"


# Mapeamentos de código → descrição legível

STATUS_DESCRICAO: dict[str, str] = {
    "AT": "Ativo",
    "PE": "Pendente",
    "CA": "Cancelado",
    "IN": "Inscrito",
    "RE": "Retificado",
    "SU": "Suspenso",
}

TIPO_DESCRICAO: dict[str, str] = {
    "IRU": "Imóvel Rural",
    "PCT": "Povos e Comunidades Tradicionais",
    "AST": "Assentamento da Reforma Agrária",
}


# ──────────────────────────────────────────────
#  Bounding Boxes aproximados dos estados (EPSG:4674)
#  Formato: (min_lon, min_lat, max_lon, max_lat)
#  Fonte: limites geográficos oficiais IBGE
# ──────────────────────────────────────────────

UF_BBOXES: dict[str, tuple[float, float, float, float]] = {
    "AC": (-73.99, -11.15, -66.63, -7.11),
    "AL": (-37.94, -10.50, -35.15, -8.81),
    "AM": (-73.79, -9.82, -56.10, 2.25),
    "AP": (-54.87, -1.23, -49.88, 4.44),
    "BA": (-46.62, -18.35, -37.34, -8.53),
    "CE": (-41.42, -7.86, -37.25, -2.78),
    "DF": (-48.29, -16.05, -47.31, -15.50),
    "ES": (-41.88, -21.30, -39.68, -17.89),
    "GO": (-53.25, -19.50, -45.91, -12.39),
    "MA": (-48.57, -10.26, -41.80, -1.04),
    "MG": (-51.05, -22.92, -39.86, -14.23),
    "MS": (-58.17, -24.07, -53.26, -17.17),
    "MT": (-61.63, -18.04, -50.22, -7.35),
    "PA": (-58.90, -9.84, -46.06, 2.59),
    "PB": (-38.77, -8.30, -34.79, -6.02),
    "PE": (-41.36, -9.48, -34.86, -7.33),
    "PI": (-45.99, -10.93, -40.37, -2.74),
    "PR": (-54.62, -26.72, -48.02, -22.52),
    "RJ": (-44.89, -23.37, -40.96, -20.76),
    "RN": (-37.26, -6.98, -34.95, -4.83),
    "RO": (-66.62, -13.69, -59.77, -7.97),
    "RR": (-64.83, -1.58, -58.88, 5.27),
    "RS": (-57.64, -33.75, -49.69, -27.08),
    "SC": (-53.84, -29.39, -48.56, -25.95),
    "SE": (-38.25, -11.57, -36.39, -9.51),
    "SP": (-53.11, -25.31, -44.16, -19.78),
    "TO": (-50.73, -13.47, -45.73, -5.17),
}


def detectar_ufs_por_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> list[str]:
    """
    Detecta quais UFs intersectam um Bounding Box.

    Usa interseção de retângulos: dois BBoxes se intersectam se
    nenhum está completamente fora do outro em qualquer eixo.

    Args:
        min_lon: Longitude mínima do BBox de busca.
        min_lat: Latitude mínima do BBox de busca.
        max_lon: Longitude máxima do BBox de busca.
        max_lat: Latitude máxima do BBox de busca.

    Returns:
        Lista de siglas UF que intersectam o BBox (ex: ["SP", "MG"]).
    """
    ufs_encontradas: list[str] = []

    for uf, (uf_min_lon, uf_min_lat, uf_max_lon, uf_max_lat) in UF_BBOXES.items():
        # Interseção de retângulos: não-interseção ocorre quando
        # um está completamente à esquerda, direita, acima ou abaixo do outro
        if (
            min_lon <= uf_max_lon
            and max_lon >= uf_min_lon
            and min_lat <= uf_max_lat
            and max_lat >= uf_min_lat
        ):
            ufs_encontradas.append(uf)

    return ufs_encontradas
