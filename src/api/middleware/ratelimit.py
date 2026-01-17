"""
Rate limiting configuration.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


def get_limiter() -> Limiter:
    """
    Cria instância do rate limiter.
    
    Usa IP do cliente como chave de identificação.
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=["100/hour"],  # Padrão: 100 requests por hora
        storage_uri="memory://",  # Em produção, usar Redis
    )
