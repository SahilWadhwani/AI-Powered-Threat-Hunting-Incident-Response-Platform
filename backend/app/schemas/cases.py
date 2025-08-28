from pydantic import BaseModel
from typing import List, Optional

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"          # low|medium|high|critical
    detection_ids: List[int] = []
    assignee: Optional[str] = None

class CaseOut(BaseModel):
    id: int
    title: str
    severity: str
    status: str
    assignee: str | None