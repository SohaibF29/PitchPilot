"""
SQLAlchemy ORM models representing Supabase PostgreSQL schema.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as pgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.constants import EMBEDDING_DIMENSIONS


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class ProfileModel(Base):
    """SaaS profiles table matching auth.users in Supabase."""

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow
    )

    api_keys: Mapped[list[ApiKeyModel]] = relationship(
        "ApiKeyModel", back_populates="profile", cascade="all, delete-orphan"
    )
    meetings: Mapped[list[MeetingModel]] = relationship(
        "MeetingModel", back_populates="profile", cascade="all, delete-orphan"
    )


class ApiKeyModel(Base):
    """Secure encrypted API keys for external services."""

    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    key_hint: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow
    )

    profile: Mapped[ProfileModel] = relationship("ProfileModel", back_populates="api_keys")


class MeetingModel(Base):
    """Meetings/pitches boardroom session data."""

    __tablename__ = "meetings"

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    pitch_text: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="created")
    thread_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    agent_outputs: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    transcript: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow
    )

    profile: Mapped[ProfileModel | None] = relationship("ProfileModel", back_populates="meetings")
    report: Mapped[ReportModel | None] = relationship(
        "ReportModel", back_populates="meeting", uselist=False, cascade="all, delete-orphan"
    )
    embeddings: Mapped[list[MeetingEmbeddingModel]] = relationship(
        "MeetingEmbeddingModel", back_populates="meeting", cascade="all, delete-orphan"
    )


class ReportModel(Base):
    """Generated PDF Report metadata and contents."""

    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    meeting_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    sections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    meeting: Mapped[MeetingModel] = relationship("MeetingModel", back_populates="report")


class MeetingEmbeddingModel(Base):
    """Embeddings table for meetings to run semantic search with pgvector."""

    __tablename__ = "meeting_embeddings"

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    meeting_id: Mapped[UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(String, nullable=False)
    embedding = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    meeting: Mapped[MeetingModel] = relationship("MeetingModel", back_populates="embeddings")
