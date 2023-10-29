from trader.roles.harvester import Harvester
from trader.roles.merchant import Merchant


class SimpleMinerTrader:
    harvester: Harvester
    merchant: Merchant

    def __init__(self, api_key: str, call_sign: str):
        self.harvester = Harvester(api_key=api_key, call_sign=call_sign)
        self.merchant = Merchant(api_key=api_key, call_sign=call_sign)

    def run_loop(self):
        # self.harvester.survey()
        self.harvester.mine()
        self.merchant.sell_cargo()
