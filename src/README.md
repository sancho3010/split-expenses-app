# Split de Gastos

Aplicación web para dividir gastos entre grupos de personas.

## Arquitectura

3 componentes independientes:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL   │
│  (Nginx)     │     │  (FastAPI)   │     │   (DB)       │
│  Puerto 3000 │     │  Puerto 8000 │     │  Puerto 5432 │
└──────────────┘     └──────────────┘     └──────────────┘
```

- **Frontend:** HTML/CSS/JS vanilla servido por Nginx. Proxy reverso hacia el backend.
- **Backend:** API REST con FastAPI + SQLAlchemy. Sin frontend, solo JSON.
- **Base de datos:** PostgreSQL 16 con migraciones Alembic.

## Desarrollo local

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/groups
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:3000/health

## Estructura del proyecto

```
src/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/           # Migraciones de DB
│   ├── app/
│   │   ├── main.py        # Entry point FastAPI
│   │   ├── config.py      # Settings (env vars)
│   │   ├── database.py    # SQLAlchemy
│   │   ├── models.py      # ORM models
│   │   ├── exceptions.py  # Errores HTTP
│   │   ├── routes/        # Endpoints API
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Lógica de negocio
│   └── tests/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── css/style.css
    └── js/
        ├── api.js         # Capa HTTP
        └── app.js         # Lógica UI
```
