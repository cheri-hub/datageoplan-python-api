"""
Rotas de Autenticação.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.dependencies import get_auth_service
from src.api.v1.schemas import AuthStatusResponse, LoginResponse, SessionInfoResponse
from src.core.exceptions import GovBrError, SessionExpiredError
from src.core.logging import get_logger
from src.services.auth_service import AuthService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Verifica status de autenticação",
    description="Retorna se existe uma sessão válida e seus detalhes.",
)
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthStatusResponse:
    """Verifica status de autenticação."""
    is_valid, session = await auth_service.validate_current_session()
    
    if is_valid and session:
        return AuthStatusResponse(
            authenticated=True,
            session=SessionInfoResponse(
                session_id=session.session_id,
                cpf=session.cpf,
                nome=session.nome,
                is_valid=session.is_valid(),
                is_govbr_authenticated=session.is_govbr_authenticated,
                is_sigef_authenticated=session.is_sigef_authenticated,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_used_at=session.last_used_at,
            ),
            message="Sessão válida",
        )
    
    return AuthStatusResponse(
        authenticated=False,
        session=None,
        message="Nenhuma sessão válida encontrada",
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Inicia autenticação Gov.br",
    description="""
    Inicia processo de autenticação interativo com Gov.br.
    
    **ATENÇÃO**: Este endpoint abre um navegador para o usuário
    selecionar o certificado digital e completar o login.
    
    O navegador será aberto na máquina onde a API está rodando.
    Use este endpoint apenas em servidores com acesso ao display
    ou configure sessão prévia manualmente.
    """,
)
async def login(
    force_new: bool = False,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Realiza login no Gov.br.
    
    Args:
        force_new: Se True, cria nova sessão mesmo se existir uma válida.
    """
    try:
        session = await auth_service.get_or_create_session(force_new=force_new)
        
        return LoginResponse(
            success=True,
            message="Login realizado com sucesso",
            session=SessionInfoResponse(
                session_id=session.session_id,
                cpf=session.cpf,
                nome=session.nome,
                is_valid=session.is_valid(),
                is_govbr_authenticated=session.is_govbr_authenticated,
                is_sigef_authenticated=session.is_sigef_authenticated,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_used_at=session.last_used_at,
            ),
        )
        
    except GovBrError as e:
        logger.error("Erro no login Gov.br", error=str(e))
        raise HTTPException(status_code=401, detail=str(e))
        
    except Exception as e:
        logger.exception("Erro inesperado no login")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post(
    "/logout",
    summary="Encerra sessão",
    description="Remove a sessão atual.",
)
async def logout(
    session_id: str | None = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Encerra sessão.
    
    Args:
        session_id: ID da sessão a encerrar. Se não informado, encerra a atual.
    """
    await auth_service.logout(session_id)
    return {"message": "Logout realizado com sucesso"}


@router.get(
    "/session",
    response_model=SessionInfoResponse | None,
    summary="Obtém informações da sessão",
    description="Retorna detalhes da sessão atual.",
)
async def get_session_info(
    auth_service: AuthService = Depends(get_auth_service),
) -> SessionInfoResponse | None:
    """Retorna informações da sessão atual."""
    info = await auth_service.get_session_info()
    
    if not info:
        return None
    
    return SessionInfoResponse(**info)
