"""Unit test configuration — sets required env vars before app imports."""

import os

# Set DATABASE_URL before any app module is imported.
# Unit tests never connect to a real DB — this just satisfies pydantic-settings.
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
