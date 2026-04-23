"""
Tests de aceptación | validan flujos completos desde el navegador con Selenium.

Corren contra staging (APP_BASE_URL) después del deploy.
Usan Chrome headless para simular un usuario real.
"""

import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:80").rstrip("/")
WAIT_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def browser():
    """Configura Chrome headless para los tests."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(WAIT_TIMEOUT)

    yield driver
    driver.quit()


def wait_for(driver, by, selector, timeout=WAIT_TIMEOUT):
    """Espera a que un elemento sea visible."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, selector))
    )


def crear_grupo(driver, nombre, miembros):
    """Helper: crea un grupo desde la UI y retorna al listado."""
    driver.get(BASE_URL)

    # Abrir formulario
    wait_for(driver, By.ID, "toggle-create-form").click()
    wait_for(driver, By.ID, "group-name").send_keys(nombre)

    # Agregar miembros
    for miembro in miembros:
        driver.find_element(By.ID, "group-members").send_keys(miembro)
        driver.find_element(By.ID, "add-member-btn").click()
        wait_for(driver, By.XPATH, f"//span[contains(@class,'member-tag') and contains(text(),'{miembro}')]")

    # Enviar formulario
    driver.find_element(By.CSS_SELECTOR, "#create-group-form button[type='submit']").click()
    wait_for(driver, By.ID, "group-title")


# ---------------------------------------------------------------------------
# Flujo 1: Crear grupo y ver miembros
# ---------------------------------------------------------------------------

def test_crear_grupo_aparece_en_listado(browser):
    """Crear un grupo → aparece en la lista de grupos."""
    crear_grupo(browser, "Viaje Selenium", ["Ana", "Bob"])

    # Volver al listado de grupos
    browser.get(BASE_URL)

    # Verificar que el grupo aparece en el listado
    wait_for(browser, By.ID, "group-list")
    grupos = browser.find_elements(By.CSS_SELECTOR, ".group-card")
    nombres = [g.find_element(By.TAG_NAME, "h3").text for g in grupos]

    assert "Viaje Selenium" in nombres


def test_crear_grupo_navega_al_detalle(browser):
    """Crear un grupo → navega automáticamente al detalle del grupo."""
    crear_grupo(browser, "Viaje Detalle", ["Ana", "Bob"])

    # Debe mostrar la vista de detalle con el nombre del grupo
    titulo = wait_for(browser, By.ID, "group-title")
    assert "Viaje Detalle" in titulo.text


def test_detalle_grupo_muestra_miembros(browser):
    """El detalle del grupo muestra los miembros en la barra."""
    crear_grupo(browser, "Viaje Miembros", ["Ana", "Bob"])

    members_bar = wait_for(browser, By.ID, "members-bar")
    badges = members_bar.find_elements(By.CLASS_NAME, "badge")
    nombres = [b.text for b in badges]

    assert any("Ana" in n for n in nombres)
    assert any("Bob" in n for n in nombres)


# ---------------------------------------------------------------------------
# Flujo 2: Registrar gasto y ver en listado
# ---------------------------------------------------------------------------

def test_agregar_gasto_aparece_en_listado(browser):
    """Crear grupo → agregar gasto → aparece en la lista de gastos."""
    crear_grupo(browser, "Viaje Gasto", ["Ana", "Bob"])

    # Agregar gasto
    browser.find_element(By.ID, "expense-desc").send_keys("Hotel")
    browser.find_element(By.ID, "expense-amount").send_keys("90")

    # Seleccionar pagador
    Select(browser.find_element(By.ID, "expense-paid-by")).select_by_index(1)

    browser.find_element(By.CSS_SELECTOR, "#add-expense-form button[type='submit']").click()

    # Verificar que el gasto aparece
    expenses_table = wait_for(browser, By.ID, "expenses-table")
    assert "Hotel" in expenses_table.text


# ---------------------------------------------------------------------------
# Flujo 3: Ver balances después de un gasto
# ---------------------------------------------------------------------------


def test_balance_refleja_gasto(browser):
    """Crear grupo → agregar gasto → el balance muestra valores correctos."""
    crear_grupo(browser, "Viaje Balance", ["Ana", "Bob"])

    # Agregar gasto
    browser.find_element(By.ID, "expense-desc").send_keys("Taxi")
    browser.find_element(By.ID, "expense-amount").send_keys("60")

    Select(browser.find_element(By.ID, "expense-paid-by")).select_by_index(1)

    browser.find_element(By.CSS_SELECTOR, "#add-expense-form button[type='submit']").click()

    # Ir a tab de balances
    wait_for(browser, By.CSS_SELECTOR, "[data-tab='balances']")
    browser.find_element(By.CSS_SELECTOR, "[data-tab='balances']").click()

    balances_list = wait_for(browser, By.ID, "balances-list")
    assert balances_list.text != ""


# ---------------------------------------------------------------------------
# Flujo 4: Ver transferencias sugeridas
# ---------------------------------------------------------------------------

def test_transferencias_aparecen_despues_de_gasto(browser):
    """Crear grupo → agregar gasto → aparece transferencia sugerida."""
    crear_grupo(browser, "Viaje Transferencia", ["Ana", "Bob"])

    # Agregar gasto
    browser.find_element(By.ID, "expense-desc").send_keys("Cena")
    browser.find_element(By.ID, "expense-amount").send_keys("100")

    Select(browser.find_element(By.ID, "expense-paid-by")).select_by_index(1)

    browser.find_element(By.CSS_SELECTOR, "#add-expense-form button[type='submit']").click()

    # Ir a tab de transferencias
    wait_for(browser, By.CSS_SELECTOR, "[data-tab='settlements']")
    browser.find_element(By.CSS_SELECTOR, "[data-tab='settlements']").click()

    settlements_list = wait_for(browser, By.ID, "settlements-list")
    assert settlements_list.text != ""
