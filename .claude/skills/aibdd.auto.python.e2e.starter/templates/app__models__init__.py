"""SQLAlchemy ORM Models。

Base 是所有 Model 的基類，用於 Alembic 自動偵測 schema 變更。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy ORM Base Class。"""
    pass


__all__ = ["Base"]
