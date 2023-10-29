import os
from typing import List, Optional, cast

from rich.console import Console

from trader.client.agent import Agent
from trader.client.client import Client
from trader.client.contract import Contract
from trader.client.market import Market, Sale
from trader.client.navigation import Navigation
from trader.client.payload import RegistrationResponse, RegistrationResponsePayload
from trader.client.registration import RegistrationRequestData
from trader.client.ship import Ship
from trader.client.system import System
from trader.client.waypoint import Waypoint
from trader.exceptions import TraderException
from trader.logic.simple_miner_trader import SimpleMinerTrader
from trader.print import print_alert, print_as_table

TOKEN_PATH = ".token"


class Trader:
    api_key: Optional[str] = None
    client: Client
    console = Console()

    def __init__(self) -> None:
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "r") as file:
                self.api_key = file.read()
        self.client = Client(api_key=self.api_key)

    def register(self, call_sign: str, faction: str) -> None:
        registration_response = self.client.register(
            data=RegistrationRequestData(
                call_sign=call_sign,
                faction=faction,
            )
        )
        with open(TOKEN_PATH, "w") as file:
            token = cast(
                RegistrationResponse,
                cast(RegistrationResponsePayload, registration_response).data,
            ).token
            file.write(token)
            self.api_key = token
            self.client = Client(api_key=token)
        self.client.ensure_api_key()
        print_alert(message=f"Registered as {call_sign}", console=self.console)

    def agent(self) -> None:
        agent_response = self.client.agent()
        agent: Agent = cast(Agent, agent_response.data)
        print_as_table(title="Agent", data=[agent], console=self.console)

    def agents(self) -> None:
        agents_response = self.client.agents()
        agents: List[Agent] = cast(List[Agent], agents_response.data)
        print_as_table(title="Agents", data=agents, console=self.console)

    def contracts(self) -> None:
        contracts_response = self.client.contracts()
        contracts: List[Contract] = cast(List[Contract], contracts_response.data)
        print_as_table(title="Contracts", data=contracts, console=self.console)

    def dock(self, call_sign: str) -> None:
        dock_response = self.client.dock(call_sign)
        print_as_table(title="Dock", data=[dock_response], console=self.console)
        print_alert(message=f"Successfully started dock!", console=self.console)

    def cargo(self, call_sign: str) -> None:
        cargo_response = self.client.cargo(call_sign)
        print_as_table(title="Cargo", data=[cargo_response], console=self.console)

    def extract(self, call_sign: str) -> None:
        extract_response = self.client.extract(call_sign)
        print_as_table(title="Extract", data=[extract_response], console=self.console)
        print_alert(message=f"Successfully started extract", console=self.console)

    def orbit(self, call_sign: str) -> None:
        orbit_response = self.client.orbit(call_sign)
        print_as_table(title="Orbit", data=[orbit_response], console=self.console)
        print_alert(message=f"Successfully started orbit!", console=self.console)

    def cooldown(self, call_sign: str) -> None:
        cooldown_response = self.client.cooldown(call_sign)
        print_as_table(title="Cooldown", data=[cooldown_response], console=self.console)

    def refuel(self, call_sign: str) -> None:
        refuel_response = self.client.refuel(call_sign)
        print_as_table(title="Refuel", data=[refuel_response], console=self.console)
        print_alert(message=f"Successfully started refuel!", console=self.console)

    def market(self, system_symbol: str, waypoint_symbol: str) -> None:
        market_response = self.client.market(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        )
        market = cast(Market, market_response.data)
        print_as_table(
            title=f"Market Exports", data=market.exports, console=self.console
        )
        print_as_table(
            title=f"Market Imports", data=market.imports, console=self.console
        )
        print_as_table(
            title=f"Market Exchange", data=market.exchange, console=self.console
        )
        print_as_table(
            title=f"Market Transactions", data=market.transactions, console=self.console
        )
        print_as_table(
            title=f"Market Trade Goods", data=market.trade_goods, console=self.console
        )

    def sell(self, call_sign: str, symbol: str, units: int) -> None:
        sale_response = self.client.sell(
            call_sign=call_sign, symbol=symbol, units=units
        )
        sale = cast(Sale, sale_response.data)
        print_as_table(
            title=f"Sale success - {call_sign} for {units} of {symbol}",
            data=[sale],
            console=self.console,
        )

    def systems(self) -> None:
        systems_response = self.client.systems()
        systems: List[System] = cast(List[System], systems_response.data)
        print_as_table(title="Systems", data=systems, console=self.console)

    def ships(self) -> None:
        ships_response = self.client.ships()
        ships: List[Ship] = cast(List[Ship], ships_response.data)
        print_as_table(title="Ships", data=ships, console=self.console)

    def ship(self, call_sign: str) -> None:
        ship_response = self.client.ship(call_sign=call_sign)
        ship: List[Ship] = cast(List[Ship], ship_response.data)
        print_as_table(title=f"Ship - {call_sign}", data=[ship], console=self.console)

    def system(self, symbol: str) -> None:
        system_response = self.client.system(symbol=symbol)
        system = cast(System, system_response.data)
        print_as_table(title="System", data=[system], console=self.console)

    def waypoints(self, system_symbol: str) -> None:
        waypoints_response = self.client.waypoints(system_symbol=system_symbol)
        waypoints = cast(List[Waypoint], waypoints_response.data)
        print_as_table(title="Waypoints", data=waypoints, console=self.console)

    def navigate(self, call_sign: str, waypoint_symbol: str) -> None:
        navigate_response = self.client.navigate(
            call_sign=call_sign, waypoint_symbol=waypoint_symbol
        )
        navigate = cast(Navigation, navigate_response.data)
        print_as_table(
            title=f"Navigation - {call_sign}", data=[navigate], console=self.console
        )

    def miner_trader_loop(self, call_sign: str) -> None:
        if not self.api_key:
            raise TraderException("No API key present to proceed")
        miner_trader = SimpleMinerTrader(api_key=self.api_key, call_sign=call_sign)
        miner_trader.run_loop()
