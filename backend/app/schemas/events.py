from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict

class EventIn(BaseModel):
    # flexible input fields; we'll normalize these
    timestamp: str
    event_module: str = Field(..., description="e.g., 'auth', 'nginx'")
    event_action: str = Field(..., description="e.g., 'ssh_login_failed', 'http_access'")
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    user: Optional[str] = None
    http_method: Optional[str] = None
    http_path: Optional[str] = None
    user_agent: Optional[str] = None
    country: Optional[str] = None
    fields: Optional[Dict[str, Any]] = None
    raw_ref: Optional[str] = None

class EventBatchIn(BaseModel):
    events: List[EventIn]

class EventOut(BaseModel):
    id: int
    event_module: str
    event_action: str
    src_ip: Optional[str] = None
    user: Optional[str] = None
    http_path: Optional[str] = None