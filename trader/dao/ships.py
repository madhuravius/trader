from typing import Optional

from sqlmodel import Field, SQLModel


class Ship(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    call_sign: str
    faction: str
    frame_name: str
    system_symbol: str
    waypoint_symbol: str
