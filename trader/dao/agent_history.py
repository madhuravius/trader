from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AgentHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    agent_symbol: str
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    ship_count: int
    in_system_count: int
    credits: int
