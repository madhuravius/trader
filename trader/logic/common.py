from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import List, Optional

from loguru import logger

from trader.client.ship import Ship
from trader.dao.squads import Squad
from trader.queues.action_queue import ActionQueue
from trader.roles.common import Common as CommonRole

DEFAULT_INTERNAL_LOOP_INTERVAL = 3


class Common(ABC):
    """
    Core logic class for ship behaviors. This basically should have common actions
    and resources that will get reused by all ship behaviors.

    The `action_queue` is very critical as it allows for us to change the course of an
    existing ship's plan (readjusting priorities, changing its work, etc.) with overrides
    for debugging and testing. This is very useful when we add ships and need squad behavior
    as it will change as soon as a ship is added.
    """

    action_queue: ActionQueue
    base_priority: int
    ship: Ship
    squad: Optional[Squad]
    roles: List[CommonRole]
    repeat: bool
    running_loop: bool = False

    def compute_role_metrics(self, **_):
        total_credits_earned = sum([role.credits_earned for role in self.roles])
        total_credits_spent = sum([role.credits_spent for role in self.roles])
        total_time_spent = sum(
            [
                int((datetime.now(UTC) - role.time_started).total_seconds())
                for role in self.roles
            ]
        )
        return (total_credits_earned, total_credits_spent, total_time_spent)

    def log_audit_performance(self, **_):
        (
            total_credits_earned,
            total_credits_spent,
            total_time_spent,
        ) = self.compute_role_metrics()

        logger.info(
            f"Logic loop complete for: {self.ship.symbol} "
            f"with {total_credits_earned - total_credits_spent} credits profit. "
            f"Total credits earned: {total_credits_earned}. Total credits spent: {total_credits_spent}. "
            f"Total time spent: {total_time_spent}."
        )

    def reset_audit_performance(self, **_):
        for role in self.roles:
            role.reset_metrics()

    def persist_audit_performance(self, event_name: str, **_):
        (
            total_credits_earned,
            total_credits_spent,
            total_time_spent,
        ) = self.compute_role_metrics()

        self.roles[0].save_to_audit_table(
            event_name=event_name,
            ship_id=self.ship.symbol,
            system_symbol=self.ship.nav.system_symbol,
            waypoint_symbol=self.ship.nav.waypoint_symbol,
            credits_earned=total_credits_earned,
            credits_spent=total_credits_spent,
            duration=total_time_spent,
        )

    @abstractmethod
    def run_loop():
        pass
