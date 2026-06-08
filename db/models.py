from datetime import datetime

from sqlalchemy import String, Boolean, Integer, BigInteger, DateTime, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(128), default=None)
    full_name: Mapped[str | None] = mapped_column(String(256), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WbAccount(Base):
    __tablename__ = "wb_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    token: Mapped[str] = mapped_column(String(512), nullable=False)
    ignore_list: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
