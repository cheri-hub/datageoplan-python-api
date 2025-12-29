"""
Exceções customizadas da aplicação.
Seguem o princípio de Single Responsibility.
"""

from typing import Any, Optional


class GovAuthException(Exception):
    """Exceção base da aplicação."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# === Exceções de Autenticação ===

class AuthenticationError(GovAuthException):
    """Erro de autenticação."""
    
    def __init__(self, message: str = "Falha na autenticação", details: Optional[dict] = None):
        super().__init__(message, code="AUTH_ERROR", details=details)


class SessionExpiredError(AuthenticationError):
    """Sessão expirada."""
    
    def __init__(self, message: str = "Sessão expirada", details: Optional[dict] = None):
        super().__init__(message, details=details)
        self.code = "SESSION_EXPIRED"


class SessionNotFoundError(AuthenticationError):
    """Sessão não encontrada."""
    
    def __init__(self, message: str = "Sessão não encontrada", details: Optional[dict] = None):
        super().__init__(message, details=details)
        self.code = "SESSION_NOT_FOUND"


class CertificateError(AuthenticationError):
    """Erro com certificado digital."""
    
    def __init__(self, message: str = "Erro no certificado digital", details: Optional[dict] = None):
        super().__init__(message, details=details)
        self.code = "CERTIFICATE_ERROR"


# === Exceções de Integração ===

class IntegrationError(GovAuthException):
    """Erro de integração com serviço externo."""
    
    def __init__(self, message: str, service: str, details: Optional[dict] = None):
        super().__init__(message, code="INTEGRATION_ERROR", details=details)
        self.service = service
        self.details["service"] = service


class GovBrError(IntegrationError):
    """Erro na integração com Gov.br."""
    
    def __init__(self, message: str = "Erro na comunicação com Gov.br", details: Optional[dict] = None):
        super().__init__(message, service="govbr", details=details)
        self.code = "GOVBR_ERROR"


class SigefError(IntegrationError):
    """Erro na integração com SIGEF."""
    
    def __init__(self, message: str = "Erro na comunicação com SIGEF", details: Optional[dict] = None):
        super().__init__(message, service="sigef", details=details)
        self.code = "SIGEF_ERROR"


class ParcelaNotFoundError(SigefError):
    """Parcela não encontrada no SIGEF."""
    
    def __init__(self, codigo: str, details: Optional[dict] = None):
        super().__init__(f"Parcela não encontrada: {codigo}", details=details)
        self.code = "PARCELA_NOT_FOUND"
        self.details["codigo_parcela"] = codigo


# === Exceções de Validação ===

class ValidationError(GovAuthException):
    """Erro de validação."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, code="VALIDATION_ERROR", details=details)
        if field:
            self.details["field"] = field


class InvalidParcelaCodeError(ValidationError):
    """Código de parcela inválido."""
    
    def __init__(self, codigo: str):
        super().__init__(
            f"Código de parcela inválido: {codigo}",
            field="codigo_parcela",
            details={"codigo": codigo, "expected_format": "UUID v4"}
        )
        self.code = "INVALID_PARCELA_CODE"
