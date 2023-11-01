from loguru import logger

from trader.logic.common import Common
from trader.roles.explorer import Explorer


class SimpleExplorer(Common):
    explorer: Explorer
    repeat: bool

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        super().__init__()
        self.explorer = Explorer(api_key=api_key, call_sign=call_sign)
        self.roles = [self.explorer]
        self.repeat = repeat
        self.ship = self.explorer.ship

    def run_loop(self):
        iteration = 1
        if self.repeat:
            logger.info(
                "Repeat option enabled, repeating the run loop upon completion!"
            )
        while True:
            self.persist_audit_performance(event_name="simple-explorer-loop.begin")
            if self.repeat:
                logger.info(f"Starting iteration {iteration} of loop")
            waypoints = self.explorer.find_optimal_path_to_explore()
            self.persist_audit_performance(event_name="simple-explorer-loop.explore")
            self.explorer.traverse_all_waypoints_and_check_markets(waypoints=waypoints)
            self.log_audit_performance()
            self.persist_audit_performance(event_name="simple-explorer-loop.finish")
            self.reset_audit_performance()
            if not self.repeat:
                break
            iteration += 1
