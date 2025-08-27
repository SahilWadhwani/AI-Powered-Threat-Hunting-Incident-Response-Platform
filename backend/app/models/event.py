from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .base import Base

class EventNormalized(Base):
    __tablename__ = "events_normalized"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    event_module: Mapped[str] = mapped_column(String(64), index=True)
    event_action: Mapped[str] = mapped_column(String(64), index=True)
    src_ip: Mapped[str | None] = mapped_column(String(45), index=True)   # IPv4/IPv6
    dst_ip: Mapped[str | None] = mapped_column(String(45), index=True)
    user: Mapped[str | None] = mapped_column(String(128), index=True)
    http_method: Mapped[str | None] = mapped_column(String(16))
    http_path: Mapped[str | None] = mapped_column(String(512), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(512))
    country: Mapped[str | None] = mapped_column(String(2))  # ISO country code
    fields_json: Mapped[dict | None] = mapped_column(JSON)
    raw_ref: Mapped[str | None] = mapped_column(String(256))  # pointer to raw log source

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))