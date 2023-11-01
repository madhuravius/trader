from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from loguru import logger

from trader.client.ship import Ship
from trader.roles.common import Common as CommonRole


class Common(ABC):
    ship: Ship
    roles: List[CommonRole]
    repeat: bool

    def compute_role_metrics(self):
        total_credits_earned = sum([role.credits_earned for role in self.roles])
        total_credits_spent = sum([role.credits_spent for role in self.roles])
        total_time_spent = sum(
            [
                int((datetime.utcnow() - role.time_started).total_seconds())
                for role in self.roles
            ]
        )
        return (total_credits_earned, total_credits_spent, total_time_spent)

    def log_audit_performance(self):
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

    def reset_audit_performance(self):
        for role in self.roles:
            role.reset_metrics()

    def persist_audit_performance(self, event_name: str):
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
