from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from dataclass_wizard import JSONWizard


@dataclass
class FleetSummaryRow(JSONWizard):
    ship_id: str
    frame_name: str
    waypoint_symbol: str
    duration: Optional[int] = None
    credits_earned: Optional[int] = None
    credits_spent: Optional[int] = None
    logic: Optional[str] = None
    activity: Optional[str] = None
    record_date: Optional[datetime] = None


@dataclass
class AgentHistoryRow(JSONWizard):
    agent_symbol: str
    ship_count: int
    in_system_count: int
    credits: int
    record_date: datetime
