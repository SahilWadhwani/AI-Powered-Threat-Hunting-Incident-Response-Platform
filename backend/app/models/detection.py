from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from .base import Base

class Detection(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    rule_id: Mapped[str | None] = mapped_column(String(128), index=True)     # for rule-based detections
    kind: Mapped[str] = mapped_column(String(16), index=True, default="rule") # "rule" | "anomaly"
    severity: Mapped[str] = mapped_column(String(16), index=True)             # "low"|"medium"|"high"|"critical"
    title: Mapped[str] = mapped_column(String(256))
    summary: Mapped[str | None] = mapped_column(String(2048))
    event_ids: Mapped[list[int] | None] = mapped_column(JSON)  # store as array in JSON for now
    features_json: Mapped[dict | None] = mapped_column(JSON)   # explainability / anomaly features
    status: Mapped[str] = mapped_column(String(16), index=True, default="open") # "open"|"closed"
    assignee: Mapped[str | None] = mapped_column(String(128))
    tags: Mapped[list[str] | None] = mapped_column(JSON)