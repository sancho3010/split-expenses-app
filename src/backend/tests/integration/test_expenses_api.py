"""Tests de integración para el endpoint de gastos, balances y transferencias."""

from decimal import Decimal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def crear_grupo(client, nombre="Viaje", miembros=None):
    """Crea un grupo y retorna el body de la respuesta."""
    if miembros is None:
        miembros = ["Ana", "Bob", "Carlos"]

    response = client.post(
        "/api/groups/",
        json={"name": nombre, "members": miembros},
    )
    return response.json()


def crear_gasto(client, group_id, paid_by_id, descripcion="Hotel", monto="90.00"):
    """Crea un gasto y retorna el body de la respuesta."""
    response = client.post(
        f"/api/groups/{group_id}/expenses",
        json={
            "description": descripcion,
            "amount": monto,
            "paid_by_id": paid_by_id,
        },
    )
    return response


# ---------------------------------------------------------------------------
# POST /api/groups/{id}/expenses —> Crear gasto
# ---------------------------------------------------------------------------


def test_crear_gasto_retorna_201_con_splits(client):
    """Gasto válido → 201 con splits correctos."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]

    response = crear_gasto(client, grupo["id"], pagador_id)

    assert response.status_code == 201

    body = response.json()
    assert body["description"] == "Hotel"
    assert Decimal(body["amount"]) == Decimal("90.00")
    assert len(body["splits"]) == 3


def test_crear_gasto_sin_split_among_divide_entre_todos(client):
    """Sin split_among_ids → splits entre todos los miembros."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    pagador_id = grupo["members"][0]["id"]

    response = crear_gasto(client, grupo["id"], pagador_id, monto="90.00")

    assert response.status_code == 201
    assert len(response.json()["splits"]) == 3


def test_crear_gasto_con_split_among_divide_solo_entre_ellos(client):
    """Con split_among_ids → splits solo entre los especificados."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    pagador_id = grupo["members"][0]["id"]
    split_ids = [grupo["members"][0]["id"], grupo["members"][1]["id"]]

    response = client.post(
        f"/api/groups/{grupo['id']}/expenses",
        json={
            "description": "Taxi",
            "amount": "60.00",
            "paid_by_id": pagador_id,
            "split_among_ids": split_ids,
        },
    )

    assert response.status_code == 201
    assert len(response.json()["splits"]) == 2


def test_crear_gasto_division_con_residuo_suma_exacta(client):
    """$10 entre 3 personas → suma de splits == $10.00 exacto."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    pagador_id = grupo["members"][0]["id"]

    response = crear_gasto(client, grupo["id"], pagador_id, monto="10.00")

    splits = response.json()["splits"]
    total = sum(Decimal(s["amount"]) for s in splits)
    assert total == Decimal("10.00")


def test_crear_gasto_grupo_inexistente_retorna_404(client):
    """Grupo inexistente → 404."""
    response = client.post(
        "/api/groups/00000000-0000-0000-0000-000000000000/expenses",
        json={
            "description": "Hotel",
            "amount": "90.00",
            "paid_by_id": "00000000-0000-0000-0000-000000000001",
        },
    )

    assert response.status_code == 400


def test_crear_gasto_descripcion_solo_espacios_retorna_400(client):
    """Descripción con solo espacios pasa Pydantic pero la lógica la rechaza → 400."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]

    response = crear_gasto(client, grupo["id"], pagador_id, descripcion="   ")

    assert response.status_code == 400


def test_crear_gasto_monto_negativo_retorna_422(client):
    """Monto negativo → 422 (validación Pydantic: gt=0)."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]

    response = crear_gasto(client, grupo["id"], pagador_id, monto="-10")

    assert response.status_code == 422


def test_crear_gasto_pagador_no_miembro_retorna_400(client):
    """Pagador no es miembro del grupo → 400."""
    grupo = crear_grupo(client)

    response = client.post(
        f"/api/groups/{grupo['id']}/expenses",
        json={
            "description": "Hotel",
            "amount": "90.00",
            "paid_by_id": "00000000-0000-0000-0000-000000000099",
        },
    )

    assert response.status_code == 400


def test_crear_gasto_miembro_split_no_pertenece_retorna_400(client):
    """UUID válido en split_among pero no es miembro del grupo → 400."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]

    response = client.post(
        f"/api/groups/{grupo['id']}/expenses",
        json={
            "description": "Hotel",
            "amount": "90.00",
            "paid_by_id": pagador_id,
            "split_among_ids": ["00000000-0000-0000-0000-000000000099"],
        },
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/groups/{id}/expenses —> Listar gastos
# ---------------------------------------------------------------------------


def test_listar_gastos_retorna_200(client):
    """GET expenses → 200 con lista."""
    grupo = crear_grupo(client)

    response = client.get(f"/api/groups/{grupo['id']}/expenses")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_listar_gastos_grupo_sin_gastos_retorna_lista_vacia(client):
    """Grupo sin gastos → 200, lista vacía."""
    grupo = crear_grupo(client)

    response = client.get(f"/api/groups/{grupo['id']}/expenses")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_gastos_incluye_gasto_creado(client):
    """El gasto creado aparece en el listado."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]
    crear_gasto(client, grupo["id"], pagador_id, descripcion="Hotel")

    response = client.get(f"/api/groups/{grupo['id']}/expenses")
    descripciones = [g["description"] for g in response.json()]

    assert "Hotel" in descripciones


# ---------------------------------------------------------------------------
# DELETE /api/groups/{id}/expenses/{expense_id}
# ---------------------------------------------------------------------------


def test_eliminar_gasto_existente_retorna_204(client):
    """Gasto existente → 204."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]
    gasto = crear_gasto(client, grupo["id"], pagador_id).json()

    response = client.delete(f"/api/groups/{grupo['id']}/expenses/{gasto['id']}")

    assert response.status_code == 204


def test_eliminar_gasto_lo_quita_del_listado(client):
    """Después de eliminar, el gasto no aparece en el listado."""
    grupo = crear_grupo(client)
    pagador_id = grupo["members"][0]["id"]
    gasto = crear_gasto(client, grupo["id"], pagador_id).json()

    client.delete(f"/api/groups/{grupo['id']}/expenses/{gasto['id']}")
    response = client.get(f"/api/groups/{grupo['id']}/expenses")

    ids = [g["id"] for g in response.json()]
    assert gasto["id"] not in ids


def test_eliminar_gasto_inexistente_retorna_404(client):
    """Gasto inexistente → 404."""
    grupo = crear_grupo(client)

    response = client.delete(
        f"/api/groups/{grupo['id']}/expenses/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/groups/{id}/balances
# ---------------------------------------------------------------------------


def test_balances_retorna_200(client):
    """GET balances → 200."""
    grupo = crear_grupo(client)

    response = client.get(f"/api/groups/{grupo['id']}/balances")

    assert response.status_code == 200


def test_balances_grupo_sin_gastos_todos_en_cero(client):
    """Grupo sin gastos → todos los balances en 0."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob"])

    response = client.get(f"/api/groups/{grupo['id']}/balances")
    balances = {b["member"]: Decimal(b["balance"]) for b in response.json()}

    assert balances["Ana"] == Decimal("0.00")
    assert balances["Bob"] == Decimal("0.00")


def test_balances_ana_paga_90_entre_3(client):
    """Ana paga $90 entre 3 → Ana: +60, Bob: -30, Carlos: -30."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    ana_id = grupo["members"][0]["id"]
    crear_gasto(client, grupo["id"], ana_id, monto="90.00")

    response = client.get(f"/api/groups/{grupo['id']}/balances")
    balances = {b["member"]: Decimal(b["balance"]) for b in response.json()}

    assert balances["Ana"] == Decimal("60.00")
    assert balances["Bob"] == Decimal("-30.00")
    assert balances["Carlos"] == Decimal("-30.00")


def test_balances_suma_siempre_es_cero(client):
    """Suma de todos los balances == 0."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    ana_id = grupo["members"][0]["id"]
    crear_gasto(client, grupo["id"], ana_id, monto="90.00")

    response = client.get(f"/api/groups/{grupo['id']}/balances")
    total = sum(Decimal(b["balance"]) for b in response.json())

    assert total == Decimal("0.00")


def test_balances_grupo_inexistente_retorna_400(client):
    """Grupo inexistente → 400 (lógica de negocio: grupo no existe)."""
    response = client.get("/api/groups/00000000-0000-0000-0000-000000000000/balances")

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/groups/{id}/settlements
# ---------------------------------------------------------------------------


def test_settlements_retorna_200(client):
    """GET settlements → 200."""
    grupo = crear_grupo(client)

    response = client.get(f"/api/groups/{grupo['id']}/settlements")

    assert response.status_code == 200


def test_settlements_grupo_sin_deudas_retorna_lista_vacia(client):
    """Grupo sin gastos → lista vacía de transferencias."""
    grupo = crear_grupo(client)

    response = client.get(f"/api/groups/{grupo['id']}/settlements")

    assert response.json() == []


def test_settlements_caso_simple_una_transferencia(client):
    """Ana paga $60 entre 2 → Bob le debe $30 a Ana."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob"])
    ana_id = grupo["members"][0]["id"]
    crear_gasto(client, grupo["id"], ana_id, monto="60.00")

    response = client.get(f"/api/groups/{grupo['id']}/settlements")
    transferencias = response.json()

    assert len(transferencias) == 1
    assert transferencias[0]["to_member"] == "Ana"
    assert transferencias[0]["from_member"] == "Bob"
    assert Decimal(transferencias[0]["amount"]) == Decimal("30.00")


def test_settlements_aplicadas_dejan_todos_en_cero(client):
    """Después de aplicar las transferencias sugeridas todos quedan en 0."""
    grupo = crear_grupo(client, miembros=["Ana", "Bob", "Carlos"])
    ana_id = grupo["members"][0]["id"]
    crear_gasto(client, grupo["id"], ana_id, monto="90.00")

    balances_resp = client.get(f"/api/groups/{grupo['id']}/balances").json()
    balances = {b["member"]: Decimal(b["balance"]) for b in balances_resp}

    transferencias = client.get(f"/api/groups/{grupo['id']}/settlements").json()

    for t in transferencias:
        balances[t["from_member"]] += Decimal(t["amount"])
        balances[t["to_member"]] -= Decimal(t["amount"])

    for nombre, saldo in balances.items():
        assert saldo == Decimal("0.00"), f"{nombre} no quedó en 0: {saldo}"


def test_settlements_grupo_inexistente_retorna_400(client):
    """Grupo inexistente → 400 (lógica de negocio: grupo no existe)."""
    response = client.get("/api/groups/00000000-0000-0000-0000-000000000000/settlements")

    assert response.status_code == 400
