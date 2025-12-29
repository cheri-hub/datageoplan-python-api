"""
Testes dos endpoints da API.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Testes de health check."""
    
    def test_health_check(self, test_client: TestClient):
        """Testa endpoint de health."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self, test_client: TestClient):
        """Testa endpoint raiz."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Gov.br Auth API"
        assert "version" in data


class TestAuthEndpoints:
    """Testes de endpoints de autenticação."""
    
    def test_auth_status_no_session(self, test_client: TestClient):
        """Testa status sem sessão."""
        response = test_client.get("/api/v1/auth/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["authenticated"] is False
        assert data["session"] is None
    
    def test_logout_no_session(self, test_client: TestClient):
        """Testa logout sem sessão ativa."""
        response = test_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200


class TestSigefEndpoints:
    """Testes de endpoints SIGEF."""
    
    def test_download_invalid_codigo(self, test_client: TestClient):
        """Testa download com código inválido."""
        response = test_client.post(
            "/api/v1/sigef/download",
            json={
                "codigo": "invalid-code",
                "tipo": "parcela",
            },
        )
        
        # Deve falhar por código inválido (422 = validation error)
        assert response.status_code == 422


class TestAPIInfo:
    """Testes de informações da API."""
    
    def test_api_v1_info(self, test_client: TestClient):
        """Testa informações da API v1."""
        response = test_client.get("/api/v1/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert "endpoints" in data
