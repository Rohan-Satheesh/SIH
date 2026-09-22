"""
Declarative base shared by every ORCA / NeerMitra ORM model.

Kept in its own module (rather than inside database.py) so that model files
can import `Base` without pulling in the live `engine`, and so Alembic's
`env.py` can import `Base.metadata` without executing any app startup code.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
