from threading import Thread
from time import sleep
from typing import List

from trader.dao.ships import Ship
from trader.logic.simple_explorer import SimpleExplorer
from trader.logic.simple_miner_trader import SimpleMinerTrader

MAP_OF_SHIP_FRAME_TO_LOGIC = {"Frigate": SimpleMinerTrader, "Probe": SimpleExplorer}
DESIRED_FLEET_DISTRIBUTION = {"Frigate": 1, "Probe": 4}


class Fleet:
    api_key: str
    ships: List[Ship]

    def __init__(self, api_key: str, ships: List[Ship]) -> None:
        self.api_key = api_key
        self.ships = ships

    def run_loop(self):
        for ship in self.ships:
            ship_loop = MAP_OF_SHIP_FRAME_TO_LOGIC[ship.frame_name](
                api_key=self.api_key, call_sign=ship.call_sign, repeat=True
            )
            thread = Thread(target=ship_loop.run_loop)
            thread.setDaemon(True)
            thread.start()
        while True:
            sleep(30)
