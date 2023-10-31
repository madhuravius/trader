from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AgentHistory(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    ship_count: int
    in_system_count: int
    credits: int
