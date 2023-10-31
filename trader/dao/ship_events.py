from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ShipEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_id: Optional[str] = Field(default=None, foreign_key="ship.id")
    created_at: datetime = Field(index=True, default=datetime.utcnow())
    event_name: str
    waypoint_symbol: Optional[str]
    system_symbol: Optional[str]
    credits_earned: Optional[int]
    credits_spent: Optional[int]
    duration: Optional[int]
