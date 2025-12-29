"""
Testes das entidades do domínio.
"""

from datetime import datetime, timedelta

import pytest

from src.domain.entities import (
    Cookie,
    JWTPayload,
    Parcela,
    ParcelaSituacao,
    Session,
    TipoExportacao,
)


class TestSession:
    """Testes da entidade Session."""
    
    def test_create_session(self):
        """Testa criação de sessão."""
        session = Session(session_id="test-123")
        
        assert session.session_id == "test-123"
        assert session.cpf is None
        assert session.is_govbr_authenticated is False
        assert session.is_sigef_authenticated is False
    
    def test_session_not_expired(self):
        """Testa sessão não expirada."""
        session = Session(
            session_id="test-123",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        
        assert session.is_expired() is False
    
    def test_session_expired(self):
        """Testa sessão expirada."""
        session = Session(
            session_id="test-123",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        
        assert session.is_expired() is True
    
    def test_session_valid(self):
        """Testa validação de sessão."""
        session = Session(
            session_id="test-123",
            is_govbr_authenticated=True,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        
        assert session.is_valid() is True
    
    def test_session_invalid_not_authenticated(self):
        """Testa sessão inválida (não autenticada)."""
        session = Session(
            session_id="test-123",
            is_govbr_authenticated=False,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        
        assert session.is_valid() is False
    
    def test_get_cookies_dict(self):
        """Testa obtenção de cookies como dict."""
        session = Session(
            session_id="test-123",
            govbr_cookies=[
                Cookie(name="token", value="abc123", domain="gov.br"),
            ],
            sigef_cookies=[
                Cookie(name="session", value="xyz789", domain="incra.gov.br"),
            ],
        )
        
        # Todos os cookies
        all_cookies = session.get_cookies_dict("all")
        assert all_cookies == {"token": "abc123", "session": "xyz789"}
        
        # Apenas Gov.br
        govbr_cookies = session.get_cookies_dict("govbr")
        assert govbr_cookies == {"token": "abc123"}
        
        # Apenas SIGEF
        sigef_cookies = session.get_cookies_dict("sigef")
        assert sigef_cookies == {"session": "xyz789"}
    
    def test_touch_updates_last_used(self):
        """Testa que touch atualiza last_used_at."""
        session = Session(session_id="test-123")
        
        assert session.last_used_at is None
        
        session.touch()
        
        assert session.last_used_at is not None


class TestParcela:
    """Testes da entidade Parcela."""
    
    def test_create_parcela(self):
        """Testa criação de parcela."""
        parcela = Parcela(codigo="A1B2C3D4-E5F6-7890-ABCD-EF1234567890")
        
        # Código deve ser normalizado para minúsculas
        assert parcela.codigo == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    
    def test_parcela_is_certificada(self):
        """Testa verificação de certificação."""
        parcela_certificada = Parcela(
            codigo="test-123",
            situacao=ParcelaSituacao.CERTIFICADA,
        )
        parcela_pendente = Parcela(
            codigo="test-456",
            situacao=ParcelaSituacao.PENDENTE,
        )
        
        assert parcela_certificada.is_certificada() is True
        assert parcela_pendente.is_certificada() is False
    
    def test_get_url_sigef(self):
        """Testa geração de URL."""
        parcela = Parcela(codigo="a1b2c3d4")
        
        url = parcela.get_url_sigef()
        
        assert url == "https://sigef.incra.gov.br/geo/parcela/detalhe/a1b2c3d4/"
    
    def test_get_download_urls(self):
        """Testa geração de URLs de download."""
        parcela = Parcela(codigo="a1b2c3d4")
        
        urls = parcela.get_download_urls()
        
        assert TipoExportacao.PARCELA in urls
        assert TipoExportacao.VERTICE in urls
        assert TipoExportacao.LIMITE in urls
        
        assert "/parcela/csv/a1b2c3d4/" in urls[TipoExportacao.PARCELA]
        assert "/vertice/csv/a1b2c3d4/" in urls[TipoExportacao.VERTICE]
        assert "/limite/csv/a1b2c3d4/" in urls[TipoExportacao.LIMITE]


class TestJWTPayload:
    """Testes da entidade JWTPayload."""
    
    def test_create_jwt_payload(self):
        """Testa criação de payload JWT."""
        payload = JWTPayload(
            cpf="12345678900",
            nome="Teste Silva",
            email="teste@example.com",
            cnpjs=["12345678000100"],
            nivel_acesso="ouro",
        )
        
        assert payload.cpf == "12345678900"
        assert payload.nome == "Teste Silva"
        assert payload.email == "teste@example.com"
        assert payload.cnpjs == ["12345678000100"]
        assert payload.nivel_acesso == "ouro"
