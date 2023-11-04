from dataclasses import dataclass
from typing import List

from dataclass_wizard import JSONWizard


@dataclass
class LeaderCredits(JSONWizard):
    agent_symbol: str
    credits: int


@dataclass
class LeaderCharts(JSONWizard):
    agent_symbol: str
    chart_count: int


@dataclass
class LeaderBoard(JSONWizard):
    most_credits: List[LeaderCredits]
    most_submitted_charts: List[LeaderCharts]


@dataclass
class ServerReset(JSONWizard):
    next: str
    frequency: str
