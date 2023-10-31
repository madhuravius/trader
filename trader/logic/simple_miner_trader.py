from loguru import logger

from trader.logic.common import Common
from trader.roles.harvester import Harvester
from trader.roles.merchant import Merchant


class SimpleMinerTrader(Common):
    harvester: Harvester
    merchant: Merchant

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        self.harvester = Harvester(api_key=api_key, call_sign=call_sign)
        self.merchant = Merchant(api_key=api_key, call_sign=call_sign)
        self.roles = [self.harvester, self.merchant]
        self.repeat = repeat
        self.ship = self.harvester.ship

    def run_loop(self):
        iteration = 1
        if self.repeat:
            logger.info(
                "Repeat option enabled, repeating the run loop upon completion!"
            )
        while True:
            self.persist_audit_performance(event_name="simple-miner-trader-loop.begin")
            if self.repeat:
                logger.info(f"Starting iteration {iteration} of loop")
            # self.harvester.survey()
            self.persist_audit_performance(event_name="simple-miner-trader-loop.mine")
            self.harvester.mine()
            self.persist_audit_performance(event_name="simple-miner-trader-loop.sell")
            self.merchant.sell_cargo()
            self.log_audit_performance()
            self.persist_audit_performance(event_name="simple-miner-trader-loop.finish")
            self.reset_audit_performance()
            if not self.repeat:
                break
            iteration += 1
