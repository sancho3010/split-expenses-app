"""Tests unitarios del servicio de balances y transferencias."""

from uuid import uuid4
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.balance_service import calculate_balances, calculate_settlements

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_member(name: str):
    """Crea un miembro falso con ID y nombre."""
    member = MagicMock()
    member.id = uuid4()
    member.name = name
    return member


def make_split(member_id, amount: Decimal):
    """Crea un split falso."""
    split = MagicMock()
    split.member_id = member_id
    split.amount = amount
    return split


def make_expense(paid_by_id, amount: Decimal, splits: list):
    """Crea un gasto falso con sus splits."""
    expense = MagicMock()
    expense.paid_by_id = paid_by_id
    expense.amount = amount
    expense.splits = splits
    return expense


def make_group(members: list):
    """Crea un grupo falso con miembros."""
    group = MagicMock()
    group.id = uuid4()
    group.members = members
    return group


def make_db_mock():
    """Retorna un mock de sesión de BD."""
    return MagicMock()


# ---------------------------------------------------------------------------
# calculate_balances —> camino feliz
# ---------------------------------------------------------------------------


def test_balance_un_gasto_entre_todos():
    """Ana paga $90 entre 3 → Ana: +60, Bob: -30, Carlos: -30."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    carlos = make_member("Carlos")
    group = make_group([ana, bob, carlos])

    splits = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
        make_split(carlos.id, Decimal("30.00")),
    ]
    expense = make_expense(ana.id, Decimal("90.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        balances = calculate_balances(db, group.id)

    assert balances["Ana"] == Decimal("60.00")
    assert balances["Bob"] == Decimal("-30.00")
    assert balances["Carlos"] == Decimal("-30.00")


def test_balance_multiples_gastos_acumulan_correctamente():
    """Ana paga $90 y Bob paga $60 entre 3 → balances acumulados."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    carlos = make_member("Carlos")
    group = make_group([ana, bob, carlos])

    splits_1 = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
        make_split(carlos.id, Decimal("30.00")),
    ]
    splits_2 = [
        make_split(ana.id, Decimal("20.00")),
        make_split(bob.id, Decimal("20.00")),
        make_split(carlos.id, Decimal("20.00")),
    ]

    expense_1 = make_expense(ana.id, Decimal("90.00"), splits_1)
    expense_2 = make_expense(bob.id, Decimal("60.00"), splits_2)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            expense_1,
            expense_2,
        ]
        balances = calculate_balances(db, group.id)

    assert balances["Ana"] == Decimal("40.00")
    assert balances["Bob"] == Decimal("10.00")
    assert balances["Carlos"] == Decimal("-50.00")


def test_balance_grupo_sin_gastos_todos_en_cero():
    """Un grupo sin gastos debe retornar todos los balances en 0."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    group = make_group([ana, bob])

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        balances = calculate_balances(db, group.id)

    assert balances["Ana"] == Decimal("0.00")
    assert balances["Bob"] == Decimal("0.00")


def test_balance_suma_siempre_es_cero():
    """La suma de todos los balances siempre debe ser 0."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    carlos = make_member("Carlos")
    group = make_group([ana, bob, carlos])

    splits = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
        make_split(carlos.id, Decimal("30.00")),
    ]
    expense = make_expense(ana.id, Decimal("90.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        balances = calculate_balances(db, group.id)

    assert sum(balances.values()) == Decimal("0.00")


def test_balance_miembro_que_pago_lo_que_le_corresponde_queda_en_cero():
    """Si Ana paga exactamente su parte, su balance debe ser 0."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    group = make_group([ana, bob])

    splits = [
        make_split(ana.id, Decimal("25.00")),
        make_split(bob.id, Decimal("25.00")),
    ]
    expense = make_expense(ana.id, Decimal("25.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        balances = calculate_balances(db, group.id)

    assert balances["Ana"] == Decimal("0.00")
    assert balances["Bob"] == Decimal("-25.00")


# ---------------------------------------------------------------------------
# calculate_balances —> camino triste
# ---------------------------------------------------------------------------


def test_balance_grupo_inexistente_lanza_error():
    """Si el grupo no existe, debe lanzar ValueError."""
    db = make_db_mock()

    with patch("app.services.balance_service.get_group_with_members", return_value=None):
        with pytest.raises(ValueError, match="grupo no existe"):
            calculate_balances(db, uuid4())


# ---------------------------------------------------------------------------
# calculate_settlements —> camino feliz
# ---------------------------------------------------------------------------


def test_transferencias_caso_simple_un_deudor_un_acreedor():
    """A le debe $30 a B → 1 transferencia de A a B por $30."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    group = make_group([ana, bob])

    splits = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
    ]
    expense = make_expense(ana.id, Decimal("60.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        transferencias = calculate_settlements(db, group.id)

    assert len(transferencias) == 1
    assert transferencias[0]["from"] == "Bob"
    assert transferencias[0]["to"] == "Ana"
    assert transferencias[0]["amount"] == Decimal("30.00")


def test_transferencias_caso_complejo_minimo_de_transacciones():
    """3 personas con deudas → número de transferencias ≤ n-1 (2)."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    carlos = make_member("Carlos")
    group = make_group([ana, bob, carlos])

    splits = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
        make_split(carlos.id, Decimal("30.00")),
    ]
    expense = make_expense(ana.id, Decimal("90.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        transferencias = calculate_settlements(db, group.id)

    assert len(transferencias) <= len(group.members) - 1


def test_transferencias_grupo_sin_deudas_retorna_lista_vacia():
    """Si todos los balances son 0, no debe haber transferencias."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    group = make_group([ana, bob])

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        transferencias = calculate_settlements(db, group.id)

    assert transferencias == []


def test_transferencias_deuda_exactamente_igual_una_sola_transferencia():
    """Dos personas con deuda exactamente igual → 1 transferencia que salda todo."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    group = make_group([ana, bob])

    splits = [
        make_split(ana.id, Decimal("50.00")),
        make_split(bob.id, Decimal("50.00")),
    ]
    expense = make_expense(ana.id, Decimal("100.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        transferencias = calculate_settlements(db, group.id)

    assert len(transferencias) == 1
    assert transferencias[0]["amount"] == Decimal("50.00")


def test_transferencias_aplicadas_dejan_todos_en_cero():
    """Después de aplicar las transferencias sugeridas, todos quedan en 0."""
    db = make_db_mock()

    ana = make_member("Ana")
    bob = make_member("Bob")
    carlos = make_member("Carlos")
    group = make_group([ana, bob, carlos])

    splits = [
        make_split(ana.id, Decimal("30.00")),
        make_split(bob.id, Decimal("30.00")),
        make_split(carlos.id, Decimal("30.00")),
    ]
    expense = make_expense(ana.id, Decimal("90.00"), splits)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        balances = calculate_balances(db, group.id)

    with patch("app.services.balance_service.get_group_with_members", return_value=group):
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [expense]
        transferencias = calculate_settlements(db, group.id)

    # Aplicar transferencias sobre los balances
    balances_copia = dict(balances)
    for t in transferencias:
        balances_copia[t["from"]] += t["amount"]
        balances_copia[t["to"]] -= t["amount"]

    for nombre, saldo in balances_copia.items():
        assert saldo == Decimal("0.00"), f"{nombre} no quedó en 0: {saldo}"
