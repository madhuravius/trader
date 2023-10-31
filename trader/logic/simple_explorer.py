from trader.logic.common import Common
from trader.roles.explorer import Explorer


class SimpleExplorer(Common):
    explorer: Explorer
    repeat: bool

    def __init__(self, api_key: str, call_sign: str, repeat: bool = False):
        super().__init__()
        self.explorer = Explorer(api_key=api_key, call_sign=call_sign)
        self.repeat = repeat
        self.ship = self.explorer.ship
