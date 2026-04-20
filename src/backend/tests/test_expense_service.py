"""Tests unitarios del servicio de gastos."""

from uuid import uuid4
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.expense_service import create_expense

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fake_refresh(obj):
    """Simula que refresh no hace nada."""
    pass


def make_db_mock():
    """Retorna un mock de sesión de BD."""
    db = MagicMock()
    db.refresh.side_effect = fake_refresh
    return db


def make_member(name: str):
    """Crea un miembro falso con ID y nombre."""
    member = MagicMock()
    member.id = uuid4()
    member.name = name
    return member


def make_group(member_names: list[str]):
    """Crea un grupo falso con miembros."""
    group = MagicMock()
    group.id = uuid4()
    group.members = [make_member(name) for name in member_names]
    return group


# ---------------------------------------------------------------------------
# Camino feliz
# ---------------------------------------------------------------------------


def test_crear_gasto_descripcion_valida_y_monto_positivo():
    """Dado descripción válida y monto > 0, debe crear el gasto."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob", "Carlos"])
    pagador_id = group.members[0].id

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        gasto = create_expense(db, group.id, pagador_id, "Hotel", Decimal("90.00"))

    assert gasto is not None
    assert gasto.description == "Hotel"
    assert gasto.amount == Decimal("90.00")
    db.commit.assert_called_once()


def test_crear_gasto_sin_especificar_split_divide_entre_todos():
    """Sin split_among_ids, el gasto se divide entre todos los miembros."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob", "Carlos"])
    pagador_id = group.members[0].id

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        create_expense(db, group.id, pagador_id, "Hotel", Decimal("90.00"))

    # Debe haber creado 1 expense + 3 splits = 4 llamadas a db.add
    assert db.add.call_count == 4


def test_crear_gasto_especificando_algunos_miembros_divide_solo_entre_ellos():
    """Con split_among_ids, el gasto se divide solo entre los especificados."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob", "Carlos"])
    pagador_id = group.members[0].id
    split_ids = [group.members[0].id, group.members[1].id]  # solo Ana y Bob

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        create_expense(db, group.id, pagador_id, "Taxi", Decimal("60.00"), split_ids)

    # 1 expense + 2 splits = 3 llamadas a db.add
    assert db.add.call_count == 3


def test_crear_gasto_division_con_residuo_suma_exacta():
    """$10 entre 3 personas: la suma de los splits debe ser exactamente $10."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob", "Carlos"])
    pagador_id = group.members[0].id
    splits_creados = []

    def capturar_add(obj):
        if hasattr(obj, "amount") and hasattr(obj, "member_id"):
            splits_creados.append(obj)

    db.add.side_effect = capturar_add

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        create_expense(db, group.id, pagador_id, "Cena", Decimal("10.00"))

    total = sum(s.amount for s in splits_creados)
    assert total == Decimal("10.00")


# ---------------------------------------------------------------------------
# Camino triste
# ---------------------------------------------------------------------------


def test_crear_gasto_descripcion_vacia_lanza_error():
    """Dada una descripción vacía, debe lanzar ValueError."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob"])
    pagador_id = group.members[0].id

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        with pytest.raises(ValueError, match="descripción"):
            create_expense(db, group.id, pagador_id, "", Decimal("50.00"))


def test_crear_gasto_monto_cero_lanza_error():
    """Dado monto = 0, debe lanzar ValueError."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob"])
    pagador_id = group.members[0].id

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        with pytest.raises(ValueError, match="mayor a 0"):
            create_expense(db, group.id, pagador_id, "Hotel", Decimal("0"))


def test_crear_gasto_monto_negativo_lanza_error():
    """Dado monto negativo, debe lanzar ValueError."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob"])
    pagador_id = group.members[0].id

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        with pytest.raises(ValueError, match="mayor a 0"):
            create_expense(db, group.id, pagador_id, "Hotel", Decimal("-10"))


def test_crear_gasto_grupo_inexistente_lanza_error():
    """Si el grupo no existe, debe lanzar ValueError."""
    db = make_db_mock()

    with patch("app.services.expense_service.get_group_with_members", return_value=None):
        with pytest.raises(ValueError, match="grupo no existe"):
            create_expense(db, uuid4(), uuid4(), "Hotel", Decimal("50.00"))


def test_crear_gasto_pagador_no_es_miembro_lanza_error():
    """Si el pagador no es miembro del grupo, debe lanzar ValueError."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob"])
    pagador_externo = uuid4()  # ID que no pertenece al grupo

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        with pytest.raises(ValueError, match="pagador no es miembro"):
            create_expense(db, group.id, pagador_externo, "Hotel", Decimal("50.00"))


def test_crear_gasto_miembro_split_no_pertenece_al_grupo_lanza_error():
    """Si un miembro en split_among no pertenece al grupo, debe lanzar ValueError."""
    db = make_db_mock()
    group = make_group(["Ana", "Bob"])
    pagador_id = group.members[0].id
    miembro_externo = uuid4()  # ID que no pertenece al grupo

    with patch("app.services.expense_service.get_group_with_members", return_value=group):
        with pytest.raises(ValueError, match="no pertenecen al grupo"):
            create_expense(db, group.id, pagador_id, "Hotel", Decimal("50.00"), [miembro_externo])


def test_crear_gasto_no_llama_bd_si_descripcion_invalida():
    """Si la descripción es inválida, no debe tocar la BD."""
    db = make_db_mock()

    with patch("app.services.expense_service.get_group_with_members", return_value=MagicMock()):
        with pytest.raises(ValueError):
            create_expense(db, uuid4(), uuid4(), "", Decimal("50.00"))

    db.add.assert_not_called()
    db.commit.assert_not_called()
