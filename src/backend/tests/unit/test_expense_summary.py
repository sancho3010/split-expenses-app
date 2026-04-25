"""Tests unitarios del comportamiento 6: totalizar saldos en resúmenes."""

from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.expense_service import delete_expense, list_expenses

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db_mock():
    """Retorna un mock de sesión de BD."""
    return MagicMock()


def make_expense_mock(description: str, amount: Decimal):
    """Crea un gasto falso para tests de listado."""
    expense = MagicMock()
    expense.description = description
    expense.amount = amount
    expense.created_at = datetime.now(timezone.utc)
    return expense


# ---------------------------------------------------------------------------
# Listar gastos
# ---------------------------------------------------------------------------


def test_listar_gastos_retorna_todos_los_gastos_del_grupo():
    """Dado un grupo con gastos, debe retornar todos sus gastos."""
    db = make_db_mock()
    gastos = [
        make_expense_mock("Hotel", Decimal("90.00")),
        make_expense_mock("Comida", Decimal("60.00")),
    ]

    all_mock = db.query.return_value.options.return_value
    all_mock = all_mock.filter.return_value.order_by.return_value
    all_mock.all.return_value = gastos

    resultado = list_expenses(db, uuid4())

    assert len(resultado) == 2


def test_listar_gastos_grupo_sin_gastos_retorna_lista_vacia():
    """Un grupo sin gastos debe retornar lista vacía."""
    db = make_db_mock()

    all_mock = db.query.return_value.options.return_value
    all_mock = all_mock.filter.return_value.order_by.return_value
    all_mock.all.return_value = []

    resultado = list_expenses(db, uuid4())

    assert resultado == []


def test_listar_gastos_total_suma_montos_correctamente():
    """La suma de los montos de los gastos debe ser el total del grupo."""
    db = make_db_mock()
    gastos = [
        make_expense_mock("Hotel", Decimal("90.00")),
        make_expense_mock("Comida", Decimal("60.00")),
        make_expense_mock("Taxi", Decimal("30.00")),
    ]

    all_mock = db.query.return_value.options.return_value
    all_mock = all_mock.filter.return_value.order_by.return_value
    all_mock.all.return_value = gastos

    resultado = list_expenses(db, uuid4())
    total = sum(g.amount for g in resultado)

    assert total == Decimal("180.00")


# ---------------------------------------------------------------------------
# Eliminar gasto
# ---------------------------------------------------------------------------


def test_eliminar_gasto_existente_retorna_true():
    """Dado un gasto existente, debe eliminarlo y retornar True."""
    db = make_db_mock()
    gasto = make_expense_mock("Hotel", Decimal("90.00"))

    db.query.return_value.filter.return_value.first.return_value = gasto

    resultado = delete_expense(db, uuid4(), uuid4())

    assert resultado is True
    db.delete.assert_called_once_with(gasto)
    db.commit.assert_called_once()


def test_eliminar_gasto_inexistente_retorna_false():
    """Si el gasto no existe, debe retornar False sin tocar la BD."""
    db = make_db_mock()

    db.query.return_value.filter.return_value.first.return_value = None

    resultado = delete_expense(db, uuid4(), uuid4())

    assert resultado is False
    db.delete.assert_not_called()
    db.commit.assert_not_called()


def test_eliminar_gasto_no_llama_commit_si_no_existe():
    """Si el gasto no existe, no debe hacer commit."""
    db = make_db_mock()

    db.query.return_value.filter.return_value.first.return_value = None

    delete_expense(db, uuid4(), uuid4())

    db.commit.assert_not_called()
