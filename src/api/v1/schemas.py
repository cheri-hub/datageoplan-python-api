"""
Schemas Pydantic para validação de requests/responses da API.
Versão mínima para cliente C#.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TipoExportacaoEnum(str, Enum):
    """Tipos de exportação disponíveis."""
    
    PARCELA = "parcela"
    VERTICE = "vertice"
    LIMITE = "limite"


# ============== Auth Schemas ==============

class SessionInfoResponse(BaseModel):
    """Informações da sessão atual."""
    
    session_id: str
    cpf: str | None
    nome: str | None
    is_valid: bool
    is_govbr_authenticated: bool
    is_sigef_authenticated: bool
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None


class AuthStatusResponse(BaseModel):
    """Status de autenticação."""
    
    authenticated: bool
    session: SessionInfoResponse | None = None
    message: str


class BrowserLoginResponse(BaseModel):
    """Resposta de login via navegador do cliente."""
    
    auth_token: str
    session_id: str
    login_url: str


class BrowserCallbackRequest(BaseModel):
    """Request para retornar dados da autenticação via navegador."""
    
    auth_token: str
    govbr_cookies: list[dict]
    sigef_cookies: list[dict] | None = None
    jwt_payload: dict | None = None


# ============== Health Schemas ==============

class HealthResponse(BaseModel):
    """Resposta de health check."""
    
    status: str
    version: str
    environment: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Resposta de erro padrão."""
    
    error: str
    detail: str | None = None
    code: str | None = None


# ============== SICAR/CAR Schemas ==============

class TemaCAR(BaseModel):
    """Informações de um tema CAR."""
    
    tema_car: str
    arquivo_modelo: str
    cor_preenchimento: str | None
    cor_contorno: str
    tipo: str  # "Polygon" ou "Point"


class GrupoCAR(BaseModel):
    """Informações de um grupo de temas CAR."""
    
    classe: str
    nome_grupo: str
    ordem: int
    num_temas: int


class GrupoTemasCAR(BaseModel):
    """Grupo com lista de temas."""
    
    classe: str
    nome_grupo: str
    ordem: int
    temas: list[TemaCAR]


class ResultadoProcessamentoCAR(BaseModel):
    """Resultado do processamento de CAR."""
    
    sucesso: bool
    recibo: str | None
    temas_processados: int
    feicoes_total: int
    arquivos_gerados: list[str]
    erros: list[str] | None = None


class ProcessedStateRequest(BaseModel):
    """Request para download processado por estado."""
    
    state: str
    polygon: str
    include_sld: bool = True
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "state": "SP",
                "polygon": "AREA_PROPERTY",
                "include_sld": True
            }
        }
    }


class ProcessedCARRequest(BaseModel):
    """Request para download processado por número CAR."""
    
    car_number: str
    include_sld: bool = True
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "car_number": "SP-3538709-4861E981046E49BC81720C879459E554",
                "include_sld": True
            }
        }
    }


class PaletaCoresResponse(BaseModel):
    """Resposta com paleta de cores dos temas."""
    
    arquivo_modelo: str
    tema_car: str
    cor_preenchimento: str | None
    cor_contorno: str
    tipo: str


# ============== CAR Consulta/Demonstrativo Schemas ==============

class CentroideCAR(BaseModel):
    """Coordenadas do centróide do imóvel."""
    
    latitude: str | None = None
    longitude: str | None = None
    lat_decimal: float | None = None
    lon_decimal: float | None = None


class SituacaoCadastroCAR(BaseModel):
    """Situação do cadastro CAR."""
    
    status: str | None = None
    registro_car: str | None = None
    condicao_externa: str | None = None
    data_analise: str | None = None
    aderiu_pra: bool | None = None
    condicao_pra: str | None = None


class DadosImovelCAR(BaseModel):
    """Dados do imóvel rural."""
    
    area_hectares: float | None = None
    modulos_fiscais: float | None = None
    municipio: str | None = None
    estado: str | None = None
    municipio_uf: str | None = None
    centroide: CentroideCAR | None = None
    data_inscricao: str | None = None
    data_ultima_retificacao: str | None = None
    houve_retificacao: bool | None = None


class CoberturaSoloCAR(BaseModel):
    """Cobertura do solo do imóvel."""
    
    remanescente_vegetacao_nativa_ha: float | None = None
    area_rural_consolidada_ha: float | None = None
    area_pousio_ha: float | None = None
    area_servidao_administrativa_ha: float | None = None


class ReservaLegalCAR(BaseModel):
    """Dados de reserva legal."""
    
    situacao: str | None = None
    area_rl_averbada_ha: float | None = None
    area_rl_aprovada_nao_averbada_ha: float | None = None
    area_rl_proposta_ha: float | None = None
    total_rl_declarada_ha: float | None = None
    area_rl_vetorizada_sobreposta_rvn_ha: float | None = None
    area_rl_em_app_ha: float | None = None
    area_rl_minima_exigida_lei_ha: float | None = None
    area_rl_compensada_de_terceiros_ha: float | None = None
    area_rl_compensada_em_terceiros_ha: float | None = None


class APPCAR(BaseModel):
    """Áreas de Preservação Permanente."""
    
    area_app_ha: float | None = None
    app_em_area_consolidada_ha: float | None = None
    app_sobreposta_rvn_ha: float | None = None


class UsoRestritoCAR(BaseModel):
    """Uso restrito."""
    
    area_uso_restrito_ha: float | None = None
    uso_restrito_sobreposta_rvn_ha: float | None = None


class RegularidadeAmbientalCAR(BaseModel):
    """Regularidade ambiental."""
    
    passivo_excedente_rl_ha: float | None = None
    area_rl_recompor_ha: float | None = None
    area_app_recompor_ha: float | None = None
    area_uso_restrito_recompor_ha: float | None = None


class SobreposicoesCAR(BaseModel):
    """Sobreposições com outras áreas."""
    
    area_sobreposicao_outros_imoveis_ha: float | None = None
    area_sobreposicao_terra_indigena_ha: float | None = None
    area_sobreposicao_unidade_conservacao_ha: float | None = None
    area_sobreposicao_assentamento_ha: float | None = None


class InformacoesAdicionaisCAR(BaseModel):
    """Informações adicionais."""
    
    area_liquida_ha: float | None = None
    sobreposicoes: SobreposicoesCAR | None = None
    restricoes: list | None = None
    tem_terra_indigena: bool | None = None
    data_demonstrativo: str | None = None


class DemonstrativoCAR(BaseModel):
    """Resposta completa do demonstrativo CAR."""
    
    situacao_cadastro: SituacaoCadastroCAR
    dados_imovel: DadosImovelCAR
    cobertura_solo: CoberturaSoloCAR
    reserva_legal: ReservaLegalCAR
    app: APPCAR
    uso_restrito: UsoRestritoCAR
    regularidade_ambiental: RegularidadeAmbientalCAR
    informacoes_adicionais: InformacoesAdicionaisCAR
    sobreposicoes: SobreposicoesCAR
