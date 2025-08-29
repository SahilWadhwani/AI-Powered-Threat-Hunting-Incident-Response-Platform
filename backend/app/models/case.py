from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from .base import Base

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), default="medium")  # low|medium|high|critical
    status: Mapped[str] = mapped_column(String(16), default="open")      # open|triaged|closed
    assignee: Mapped[str | None] = mapped_column(String(128))
    detection_ids_json: Mapped[list[int] | None] = mapped_column(Text)   # store as comma-separated for MVP

    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="case", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    author: Mapped[str] = mapped_column(String(128))  # store email for simplicity
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    body: Mapped[str] = mapped_column(Text)

    case: Mapped["Case"] = relationship("Case", back_populates="comments")  