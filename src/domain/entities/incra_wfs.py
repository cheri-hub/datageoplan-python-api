"""
Entidades de domínio para consulta de parcelas INCRA via WFS GeoOne.

Enums para camadas, status de certificação e mapeamentos auxiliares.
"""

from enum import Enum


class CamadaIncra(str, Enum):
    """Camadas WFS disponíveis no GeoOne GeoINCRA."""

    SIGEF_PARTICULAR = "sigef_particular"
    SIGEF_PUBLICO = "sigef_publico"
    SNCI_PRIVADO = "snci_privado"
    SNCI_PUBLICO = "snci_publico"
    ASSENTAMENTOS = "assentamentos"
    QUILOMBOLAS = "quilombolas"
    PENDENTES_TITULACAO = "pendentes_titulacao"


class StatusCertificacao(str, Enum):
    """Status de certificação da parcela SIGEF."""

    CERTIFICADA = "CERTIFICADA"
    REGISTRADA = "REGISTRADA"
    NAO_CERTIFICADA = "NÃO CERTIFICADA"


# ──────────────────────────────────────────────
#  Mapeamento camada → layer name no GeoServer
# ──────────────────────────────────────────────

CAMADA_LAYER_MAP: dict[str, str] = {
    "sigef_particular": "GeoINCRA:certificado_sigef_privado",
    "sigef_publico": "GeoINCRA:certificado_sigef_publico",
    "snci_privado": "GeoINCRA:snci_privado",
    "snci_publico": "GeoINCRA:snci_publico",
    "assentamentos": "GeoINCRA:assentamentos",
    "quilombolas": "GeoINCRA:quilombolas",
    "pendentes_titulacao": "GeoINCRA:pendentes_titulacao",
}

CAMADA_DESCRICAO: dict[str, str] = {
    "sigef_particular": "Imóveis Certificados SIGEF - Particular",
    "sigef_publico": "Imóveis Certificados SIGEF - Público",
    "snci_privado": "SNCI Privado",
    "snci_publico": "SNCI Público",
    "assentamentos": "Assentamentos da Reforma Agrária",
    "quilombolas": "Territórios Quilombolas",
    "pendentes_titulacao": "Pendentes de Titulação",
}

# ──────────────────────────────────────────────
#  Mapeamento UF numérico IBGE → sigla
# ──────────────────────────────────────────────

UF_ID_PARA_SIGLA: dict[int, str] = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA",
    16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
    24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE",
    29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT",
    52: "GO", 53: "DF",
}

# Campos retornados quando geometria não é solicitada (camada SIGEF)
PROPERTY_NAMES_SIGEF = (
    "parcela_codigo,rt,art,situacao_i,codigo_imo,"
    "data_submi,data_aprov,status,nome_area,"
    "registro_m,registro_d,municipio_,uf_id"
)
