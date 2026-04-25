"""
Smoke tests | verifican que el sistema está vivo y funcional después del deploy.

Corren contra la URL real del ALB inyectada via APP_BASE_URL.
Van más allá de un simple healthcheck: validan que los componentes
realmente están activos y pueden procesar operaciones básicas de lectura.
"""

import os
import httpx
import pytest

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")


# ---------------------------------------------------------------------------
# Backend: Health y conectividad
# ---------------------------------------------------------------------------


def test_health_check_retorna_200():
    """GET /health → 200 con status ok y database healthy."""
    response = httpx.get(f"{BASE_URL}/health", timeout=10)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "healthy"


def test_api_grupos_retorna_200():
    """GET /api/groups/ → 200 (backend + DB responden correctamente)."""
    response = httpx.get(f"{BASE_URL}/api/groups/", timeout=10)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Frontend: Servicio y contenido
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


def test_frontend_carga_assets():
    """GET / → el HTML referencia archivos CSS y JS (assets cargados correctamente)."""
    response = httpx.get(f"{BASE_URL}/", timeout=10)
    html = response.text

    assert ".css" in html, "El frontend no referencia ningún archivo CSS"
    assert ".js" in html, "El frontend no referencia ningún archivo JS"
