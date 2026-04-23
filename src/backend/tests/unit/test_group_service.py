"""Tests unitarios del servicio de grupos."""

from unittest.mock import MagicMock

import pytest

from app.services.group_service import create_group

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fake_refresh(obj):
    """Simula que refresh no hace nada (el objeto ya tiene sus datos)."""
    pass


def make_db_mock():
    """Retorna un mock de sesión de BD que simula add/commit/refresh."""
    db = MagicMock()

    db.refresh.side_effect = fake_refresh
    return db


# ---------------------------------------------------------------------------
# Camino feliz
# ---------------------------------------------------------------------------


def test_crear_grupo_con_nombre_y_dos_miembros_retorna_grupo():
    """Dado un nombre válido y 2 miembros, debe retornar el grupo creado."""
    db = make_db_mock()
    grupo = create_group(db, "Viaje a Cartagena", ["Ana", "Bob"])

    assert grupo is not None
    assert grupo.name == "Viaje a Cartagena"
    assert len(grupo.members) == 2

    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_crear_grupo_con_nombre_exactamente_100_caracteres():
    """Dado un nombre con exactamente 100 caracteres, debe crear el grupo."""
    db = make_db_mock()
    nombre = "A" * 100
    grupo = create_group(db, nombre, ["Ana", "Bob"])

    assert grupo.name == nombre


def test_crear_grupo_elimina_espacios_del_nombre():
    """Dado un nombre con espacios al inicio/fin, debe limpiarlos."""
    db = make_db_mock()
    grupo = create_group(db, "  Viaje  ", ["Ana", "Bob"])

    assert grupo.name == "Viaje"


# ---------------------------------------------------------------------------
# Camino triste
# ---------------------------------------------------------------------------


def test_crear_grupo_nombre_vacio_lanza_error():
    """Dado un nombre vacío, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="obligatorio"):
        create_group(db, "", ["Ana", "Bob"])


def test_crear_grupo_nombre_solo_espacios_lanza_error():
    """Dado un nombre con solo espacios, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="obligatorio"):
        create_group(db, "   ", ["Ana", "Bob"])


def test_crear_grupo_nombre_mayor_100_caracteres_lanza_error():
    """Dado un nombre con más de 100 caracteres, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="100 caracteres"):
        create_group(db, "A" * 101, ["Ana", "Bob"])


def test_crear_grupo_sin_miembros_lanza_error():
    """Dado un nombre válido y sin miembros, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="al menos 2 miembros"):
        create_group(db, "Viaje", [])


def test_crear_grupo_con_un_miembro_lanza_error():
    """Dado un nombre válido y un solo miembro, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="al menos 2 miembros"):
        create_group(db, "Viaje", ["Ana"])


def test_crear_grupo_con_miembros_duplicados_lanza_error():
    """Dados miembros con nombres duplicados, debe lanzar ValueError."""
    db = make_db_mock()
    with pytest.raises(ValueError, match="únicos"):
        create_group(db, "Viaje", ["Ana", "Ana", "Bob"])


def test_crear_grupo_no_llama_bd_si_nombre_invalido():
    """Si el nombre es inválido, no debe tocar la BD."""
    db = make_db_mock()
    with pytest.raises(ValueError):
        create_group(db, "", ["Ana", "Bob"])

    db.add.assert_not_called()
    db.commit.assert_not_called()
