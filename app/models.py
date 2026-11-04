from datetime import datetime, date

from sqlalchemy import String, JSON, Date, DateTime, func, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    capacity: Mapped[int] = mapped_column(
        nullable=False
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False
    )
    amenities: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="member"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    code_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

class AuthSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

class Reservation(Base):
    __tablename__ = "reservations"

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "reservation_date",
            "slot_id",
            name="uq_reservation_room_date_slot"
        ),
        CheckConstraint(
            "slot_id BETWEEN 1 AND 7",
            name="ck_reservations_slot_id"
        )
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    room_id: Mapped[str] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    reservation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    slot_id: Mapped[int] = mapped_column(
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    note: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )