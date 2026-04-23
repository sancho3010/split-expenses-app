# Splitr — Split de Gastos

Web app para dividir gastos entre grupos de personas. Permite registrar gastos compartidos, calcular balances y generar las transferencias mínimas para saldar deudas.

**Stack:** FastAPI + PostgreSQL + HTML/CSS · **CI/CD:** GitHub Actions + Terraform + AWS ECS

**Estudiantes:** Santiago Higuita · Isis Amaya · Santiago Rozo · Samuel Oviedo

---

## Índice

- [Arquitectura](#arquitectura)
- [Desarrollo local](#desarrollo-local)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Estrategia de ramas](#estrategia-de-ramas)
- [Pipeline CI/CD](#pipeline-cicd)
- [Tests](#tests)

---

## Arquitectura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│   (Nginx)    │     │  (FastAPI)   │     │    (DB)      │
│  Puerto 3000 │     │  Puerto 8000 │     │  Puerto 5432 │
└──────────────┘     └──────────────┘     └──────────────┘
```

- **Frontend:** HTML/CSS/JS vanilla servido por Nginx. Proxy reverso hacia el backend.
- **Backend:** API REST con FastAPI + SQLAlchemy. Retorna JSON.
- **Base de datos:** PostgreSQL 16 con migraciones Alembic.

---

## Desarrollo local

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/groups |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## Estructura del proyecto

```
.
├── .github/
│   └── workflows/
│       ├── ci-backend.yml      # CI del backend
│       ├── ci-frontend.yml     # CI del frontend
│       ├── ci-database.yml     # CI de migraciones
│       └── cd.yml              # CD a staging y producción
├── src/
│   ├── docker-compose.yml
│   ├── base/
│   │   └── infra/              # IaC compartida (cluster ECS, ALB, security groups)
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── alembic/            # Migraciones de DB
│   │   ├── app/
│   │   │   ├── main.py         # Entry point FastAPI
│   │   │   ├── config.py       # Settings (env vars)
│   │   │   ├── database.py     # SQLAlchemy
│   │   │   ├── models.py       # ORM models
│   │   │   ├── exceptions.py   # Errores HTTP
│   │   │   ├── routes/         # Endpoints API
│   │   │   ├── schemas/        # Pydantic schemas
│   │   │   └── services/       # Lógica de negocio
│   │   ├── infra/              # IaC backend (ECS service, target group)
│   │   └── tests/
│   │       ├── unit/           # Tests unitarios (lógica pura, sin BD)
│   │       └── integration/    # Tests de integración (rutas + BD)
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── index.html
│   │   ├── css/style.css
│   │   ├── infra/              # IaC frontend (ECS service, target group)
│   │   └── js/
│   │       ├── api.js          # Capa HTTP
│   │       └── app.js          # Lógica UI
│   ├── database/
│   │   ├── Dockerfile
│   │   ├── infra/              # IaC database (RDS PostgreSQL)
│   │   └── init/
│   └── tests/
│       ├── acceptance/         # Tests de aceptación con Selenium (CD staging)
│       └── smoke/              # Tests de humo (CD producción)
└── .gitignore
```

---

## Estrategia de ramas

Trunk Based Development simplificado dentro de un monorepo.

1. Crear rama corta desde `main`: `feature/nombre-estudiante`
2. Trabajar los cambios
3. `git commit` — el pre-commit hook intercepta y corre localmente:
   - Black (formato)
   - Pylint (linting)
   - Tests unitarios
   - Si falla → commit bloqueado
   - Si pasa → commit se hace
4. `git push origin feature/nombre-estudiante`
5. Abrir PR desde `feature/nombre-estudiante` → `main`
6. El CI corre automáticamente en el PR
7. Si el CI pasa → se mergea a `main` → el CD se dispara

---

## Pipeline CI/CD

### CI — por componente (solo corre si hubo cambios en su carpeta)

| Workflow | Trigger | Valida |
|---|---|---|
| `ci-backend.yml` | cambios en `src/backend/app/` o `src/backend/tests/` | linters, tests unitarios, tests integración, Sonar, build imagen |
| `ci-frontend.yml` | cambios en `src/frontend/` | linters, build imagen |
| `ci-database.yml` | cambios en `src/database/` o `src/backend/alembic/` | migraciones Alembic corren sin errores, son reversibles, esquema consistente |

### CD — deploy selectivo en secuencia

Solo redesplega el componente que cambió. Orden garantizado:

```
database → backend → frontend
     ↓
test-staging (aceptación + E2E + seguridad)
     ↓
deploy-prod (mismo orden)
     ↓
smoke-test-prod
     ↓
rollback-prod (si smoke tests fallan)
  → automático: revierte al task definition anterior en ECS
```

**Botón de pánico (rollback manual):** `workflow_dispatch` en `cd.yml` con el ARN de la versión a la que revertir.

Los tests de staging corren siempre contra lo que está desplegado — validan que el cambio parcial no rompió la integración con los demás componentes.

---

## Tests

| Tipo | Dónde corre | Qué valida |
|---|---|---|
| Unitarios | Pre-commit + CI | Lógica de negocio pura (balances, transferencias) sin BD ni servidor |
| Integración | CI backend | Rutas HTTP + BD real en contenedor |
| Aceptación | CD staging | Flujo completo de usuario con Selenium |
| Seguridad | CD staging | OWASP ZAP contra el ALB |
| Humo | CD producción | `/health` responde 200, endpoints principales vivos |
