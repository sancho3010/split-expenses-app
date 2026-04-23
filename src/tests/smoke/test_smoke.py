"""
Smoke tests | verifican que el sistema está vivo después del deploy a producción.

Corren contra la URL real del ALB inyectada via APP_BASE_URL.
No prueban lógica de negocio, solo que los endpoints principales responden.
"""

import os
import httpx
import pytest

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")


# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------

def test_health_check_retorna_200():
    """GET /health → 200 con status ok y database healthy."""
    response = httpx.get(f"{BASE_URL}/health", timeout=10)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "healthy"


def test_api_grupos_retorna_200():
    """GET /api/groups/ → 200 (la API está respondiendo)."""
    response = httpx.get(f"{BASE_URL}/api/groups/", timeout=10)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

def test_frontend_retorna_200():
    """GET / → 200 (nginx está sirviendo el frontend)."""
    response = httpx.get(f"{BASE_URL}/", timeout=10)

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_frontend_contiene_titulo():
    """GET / → el HTML contiene el título de la app."""
    response = httpx.get(f"{BASE_URL}/", timeout=10)

    assert "Splitwise Lite" in response.text
