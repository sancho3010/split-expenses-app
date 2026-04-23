"""Tests de integración para el endpoint de grupos."""

# ---------------------------------------------------------------------------
# POST /api/groups/ — Crear grupo
# ---------------------------------------------------------------------------


def test_crear_grupo_retorna_201_con_datos(client):
    """Dado nombre válido y 2+ miembros → 201 con id, name y members."""
    response = client.post(
        "/api/groups/",
        json={"name": "Viaje a Cartagena", "members": ["Ana", "Bob"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Viaje a Cartagena"
    assert len(body["members"]) == 2
    assert "id" in body


def test_crear_grupo_persiste_en_bd(client):
    """El grupo creado debe ser recuperable con GET."""
    post = client.post(
        "/api/groups/",
        json={"name": "Viaje a Medellín", "members": ["Ana", "Bob"]},
    )
    group_id = post.json()["id"]

    get = client.get(f"/api/groups/{group_id}")

    assert get.status_code == 200
    assert get.json()["name"] == "Viaje a Medellín"


def test_crear_grupo_nombre_exactamente_100_caracteres(client):
    """Nombre con exactamente 100 caracteres → 201."""
    response = client.post(
        "/api/groups/",
        json={"name": "A" * 100, "members": ["Ana", "Bob"]},
    )

    assert response.status_code == 201


def test_crear_grupo_nombre_vacio_retorna_400(client):
    """Nombre con solo espacios pasa Pydantic pero la lógica lo rechaza → 400."""
    response = client.post(
        "/api/groups/",
        json={"name": "   ", "members": ["Ana", "Bob"]},
    )

    assert response.status_code == 400


def test_crear_grupo_nombre_mayor_100_caracteres_retorna_400(client):
    """Nombre > 100 caracteres → 422 (validación Pydantic: max_length=100)."""
    response = client.post(
        "/api/groups/",
        json={"name": "A" * 101, "members": ["Ana", "Bob"]},
    )

    assert response.status_code == 422


def test_crear_grupo_un_miembro_retorna_400(client):
    """Un solo miembro → 422 (validación Pydantic: min_length=2 en lista)."""
    response = client.post(
        "/api/groups/",
        json={"name": "Viaje", "members": ["Ana"]},
    )

    assert response.status_code == 422


def test_crear_grupo_sin_miembros_retorna_400(client):
    """Sin miembros → 422 (validación Pydantic: min_length=2 en lista)."""
    response = client.post(
        "/api/groups/",
        json={"name": "Viaje", "members": []},
    )

    assert response.status_code == 422


def test_crear_grupo_miembros_duplicados_retorna_400(client):
    """Miembros duplicados → 400."""
    response = client.post(
        "/api/groups/",
        json={"name": "Viaje", "members": ["Ana", "Ana", "Bob"]},
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/groups/ — Listar grupos
# ---------------------------------------------------------------------------


def test_listar_grupos_retorna_200(client):
    """GET /api/groups/ → 200 con lista."""
    response = client.get("/api/groups/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_grupos_incluye_grupo_creado(client):
    """El grupo recién creado aparece en el listado."""
    client.post(
        "/api/groups/",
        json={"name": "Viaje a Bogotá", "members": ["Ana", "Bob"]},
    )

    response = client.get("/api/groups/")
    nombres = [g["name"] for g in response.json()]

    assert "Viaje a Bogotá" in nombres


# ---------------------------------------------------------------------------
# GET /api/groups/{id} — Detalle de grupo
# ---------------------------------------------------------------------------


def test_obtener_grupo_inexistente_retorna_404(client):
    """Grupo con ID inexistente → 404."""
    response = client.get("/api/groups/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
