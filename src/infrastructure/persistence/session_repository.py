"""
Repositório de sessões em arquivo JSON.

Implementação simples para uso on-premise,
onde sessões são armazenadas em disco.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.core.exceptions import SessionExpiredError
from src.core.logging import get_logger
from src.domain.entities import Cookie, JWTPayload, Session
from src.domain.interfaces import ISessionRepository

logger = get_logger(__name__)


class FileSessionRepository(ISessionRepository):
    """
    Repositório que persiste sessões em arquivos JSON.
    
    Cada sessão é salva em um arquivo separado para
    facilitar gerenciamento e evitar conflitos.
    """
    
    def __init__(self, sessions_dir: Path | None = None):
        """
        Inicializa o repositório.
        
        Args:
            sessions_dir: Diretório para salvar sessões.
                         Se None, usa configuração padrão.
        """
        self.sessions_dir = sessions_dir or get_settings().sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "FileSessionRepository inicializado",
            sessions_dir=str(self.sessions_dir),
        )
    
    def _get_session_path(self, session_id: str) -> Path:
        """Retorna caminho do arquivo de uma sessão."""
        return self.sessions_dir / f"session_{session_id}.json"
    
    def _session_to_dict(self, session: Session) -> dict[str, Any]:
        """Converte Session para dicionário serializável."""
        return {
            "session_id": session.session_id,
            "cpf": session.cpf,
            "nome": session.nome,
            "jwt_payload": {
                "cpf": session.jwt_payload.cpf,
                "nome": session.jwt_payload.nome,
                "email": session.jwt_payload.email,
                "access_token": session.jwt_payload.access_token,
                "id_token": session.jwt_payload.id_token,
                "cnpjs": session.jwt_payload.cnpjs,
                "nivel_acesso": session.jwt_payload.nivel_acesso,
                "raw": session.jwt_payload.raw,
            } if session.jwt_payload else None,
            "govbr_cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                    "expires": c.expires,
                    "http_only": c.http_only,
                    "secure": c.secure,
                    "same_site": c.same_site,
                }
                for c in session.govbr_cookies
            ],
            "sigef_cookies": [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain,
                    "path": c.path,
                    "expires": c.expires,
                    "http_only": c.http_only,
                    "secure": c.secure,
                    "same_site": c.same_site,
                }
                for c in session.sigef_cookies
            ],
            "local_storage": session.local_storage,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "last_used_at": session.last_used_at.isoformat() if session.last_used_at else None,
            "is_govbr_authenticated": session.is_govbr_authenticated,
            "is_sigef_authenticated": session.is_sigef_authenticated,
        }
    
    def _dict_to_session(self, data: dict[str, Any]) -> Session:
        """Converte dicionário para Session."""
        jwt_data = data.get("jwt_payload")
        jwt_payload = None
        if jwt_data:
            jwt_payload = JWTPayload(
                cpf=jwt_data["cpf"],
                nome=jwt_data["nome"],
                email=jwt_data.get("email"),
                access_token=jwt_data.get("access_token"),
                id_token=jwt_data.get("id_token"),
                cnpjs=jwt_data.get("cnpjs", []),
                nivel_acesso=jwt_data.get("nivel_acesso", "bronze"),
                raw=jwt_data.get("raw", {}),
            )
        
        return Session(
            session_id=data["session_id"],
            cpf=data.get("cpf"),
            nome=data.get("nome"),
            jwt_payload=jwt_payload,
            govbr_cookies=[
                Cookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c["domain"],
                    path=c.get("path", "/"),
                    expires=c.get("expires"),
                    http_only=c.get("http_only", False),
                    secure=c.get("secure", False),
                    same_site=c.get("same_site", "Lax"),
                )
                for c in data.get("govbr_cookies", [])
            ],
            sigef_cookies=[
                Cookie(
                    name=c["name"],
                    value=c["value"],
                    domain=c["domain"],
                    path=c.get("path", "/"),
                    expires=c.get("expires"),
                    http_only=c.get("http_only", False),
                    secure=c.get("secure", False),
                    same_site=c.get("same_site", "Lax"),
                )
                for c in data.get("sigef_cookies", [])
            ],
            local_storage=data.get("local_storage", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            last_used_at=datetime.fromisoformat(data["last_used_at"]) if data.get("last_used_at") else None,
            is_govbr_authenticated=data.get("is_govbr_authenticated", False),
            is_sigef_authenticated=data.get("is_sigef_authenticated", False),
        )
    
    async def save(self, session: Session) -> None:
        """Persiste uma sessão em arquivo JSON."""
        path = self._get_session_path(session.session_id)
        data = self._session_to_dict(session)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(
            "Sessão salva",
            session_id=session.session_id,
            path=str(path),
        )
    
    async def load(self, session_id: str) -> Session | None:
        """Carrega uma sessão pelo ID."""
        path = self._get_session_path(session_id)
        
        if not path.exists():
            logger.debug("Sessão não encontrada", session_id=session_id)
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        session = self._dict_to_session(data)
        logger.info("Sessão carregada", session_id=session_id)
        return session
    
    async def load_latest(self) -> Session | None:
        """Carrega a sessão mais recente."""
        sessions = await self.list_all()
        
        if not sessions:
            return None
        
        # Ordena por data de criação, mais recente primeiro
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions[0]
    
    async def delete(self, session_id: str) -> None:
        """Remove uma sessão."""
        path = self._get_session_path(session_id)
        
        if path.exists():
            path.unlink()
            logger.info("Sessão removida", session_id=session_id)
    
    async def list_all(self) -> list[Session]:
        """Lista todas as sessões."""
        sessions: list[Session] = []
        
        for path in self.sessions_dir.glob("session_*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(self._dict_to_session(data))
            except Exception as e:
                logger.warning(
                    "Erro ao carregar sessão",
                    path=str(path),
                    error=str(e),
                )
        
        return sessions


def create_new_session() -> Session:
    """Factory function para criar nova sessão."""
    return Session(session_id=str(uuid.uuid4()))
