from datetime import UTC, datetime, timedelta
from threading import Thread
from time import sleep
from typing import List, Optional, Sequence, cast

from loguru import logger
from rich.console import Console
from sqlmodel import Session, select

from trader.client.agent import Agent
from trader.client.client import Client
from trader.client.contract import Contract
from trader.client.market import Market, PurchaseOrSale
from trader.client.navigation import FlightModes, Navigation, NavigationRequestPatch
from trader.client.payload import (
    RegistrationResponse,
    RegistrationResponsePayload,
    StatusPayload,
)
from trader.client.registration import RegistrationRequestData
from trader.client.ship import Ship
from trader.client.ship_purchase import ShipPurchase
from trader.client.shipyard import Shipyard
from trader.client.system import System
from trader.client.waypoint import Waypoint
from trader.dao.agent_histories import (
    get_agent_histories,
    get_agent_histories_by_date_cutoff,
    save_agent_history,
)
from trader.dao.dao import DAO
from trader.dao.markets import save_client_market
from trader.dao.ships import Ship as ShipDAO
from trader.dao.ships import get_ship, get_ship_events, get_ships, save_client_ships
from trader.dao.shipyards import save_client_shipyard
from trader.dao.waypoints import save_client_waypoints
from trader.exceptions import TraderClientException
from trader.fleet.fleet import Fleet
from trader.logic.leader import Leader
from trader.logic.simple_explorer import SimpleExplorer
from trader.logic.simple_miner import SimpleMiner
from trader.logic.simple_trader import SimpleTrader
from trader.print.models import AgentHistoryRow, FleetSummaryRow
from trader.print.print import print_alert, print_as_table
from trader.util.keys import read_api_key_from_disk, write_api_key_to_disk

DEFAULT_TIMEOUT_TO_RUN_MAIN_TRADER_LOOP = 300


class Trader:
    api_key: Optional[str] = None
    client: Client
    console = Console()
    dao: DAO

    def __init__(
        self, api_key: Optional[str] = None, disable_background_processes: bool = False
    ) -> None:
        if api_key:
            # this does not persist the API key, can be used for overriding clients
            self.api_key = api_key
        else:
            self.api_key = read_api_key_from_disk()
        self.client = Client(
            api_key=self.api_key,
            disable_background_processes=disable_background_processes,
        )
        self.dao = DAO()
        if not disable_background_processes:
            thread = Thread(target=self.run_loop)
            thread.daemon = True
            thread.start()

    def run_loop(self):
        while True:
            sleep(DEFAULT_TIMEOUT_TO_RUN_MAIN_TRADER_LOOP)
            self.agent(silent=True)
            self.ships(silent=True)

    def status(self) -> None:
        status_response = self.client.status()
        status = cast(StatusPayload, status_response)
        print_as_table(
            title="Leaderboard (Credits)",
            data=status.leaderboards.most_credits,
            console=self.console,
        )
        print_as_table(
            title="Leaderboard (Submitted Charts)",
            data=status.leaderboards.most_submitted_charts,
            console=self.console,
        )
        print_alert(
            message=f"Next server reset on {status.server_resets.next} at {status.server_resets.frequency} interval",
            console=self.console,
        )

    def register(self, call_sign: str, faction: str) -> None:
        registration_response = self.client.register(
            data=RegistrationRequestData(
                call_sign=call_sign,
                faction=faction,
            )
        )
        token = cast(
            RegistrationResponse,
            cast(RegistrationResponsePayload, registration_response).data,
        ).token
        write_api_key_to_disk(token)
        self.api_key = token
        self.client = Client(api_key=token)
        self.client.core_client.ensure_api_key()
        print_alert(message=f"Registered as {call_sign}", console=self.console)

    def agent(self, silent: bool = False) -> None:
        agent_response = self.client.agent()
        agent: Agent = cast(Agent, agent_response.data)
        if not silent:
            print_as_table(title="Agent", data=[agent], console=self.console)

        agent_histories = get_agent_histories_by_date_cutoff(
            engine=self.dao.engine,
            cutoff=datetime.now(UTC)
            - timedelta(seconds=DEFAULT_TIMEOUT_TO_RUN_MAIN_TRADER_LOOP),
        )
        if not agent_histories:
            ships = self.client.ships()
            ship_count = 0
            in_system_count = 0
            if ships.data:
                ship_count = len(ships.data)
                in_system_count = len(
                    set([ship.nav.system_symbol for ship in ships.data])
                )
            save_agent_history(
                engine=self.dao.engine,
                agent_symbol=agent.symbol,
                credits=agent.credits,
                ship_count=ship_count,
                in_system_count=in_system_count,
            )

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

    def set_flight_mode(self, call_sign: str, flight_mode: FlightModes) -> None:
        self.client.set_flight_mode(
            call_sign=call_sign, data=NavigationRequestPatch(flight_mode=flight_mode)
        )
        print_alert(
            message=f"Successfully set flight mode to: {flight_mode}",
            console=self.console,
        )

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
        if market.transactions:
            print_as_table(
                title=f"Market Transactions",
                data=market.transactions,
                console=self.console,
            )
        if market.trade_goods:
            print_as_table(
                title=f"Market Trade Goods",
                data=market.trade_goods,
                console=self.console,
            )
        save_client_market(
            engine=self.dao.engine, market=market, system_symbol=system_symbol
        )

    def shipyard(self, system_symbol: str, waypoint_symbol: str) -> None:
        market_response = self.client.shipyard(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        )
        shipyard = cast(Shipyard, market_response.data)
        types = ""
        if shipyard.ship_types:
            types = ", ".join(
                [ship_type.ship_type for ship_type in shipyard.ship_types]
            )

        if shipyard.ships:
            print_as_table(
                title=f"Shipyard Ships at {waypoint_symbol} (Possible: {types})",
                data=shipyard.ships,
                console=self.console,
            )
        else:
            print_alert(
                message=f"No ships found at {waypoint_symbol} (Possible: {types})",
                console=self.console,
            )
        save_client_shipyard(
            engine=self.dao.engine, shipyard=shipyard, system_symbol=system_symbol
        )

    def purchase_ship(self, waypoint_symbol: str, ship_type: str):
        ship_purchase_response = self.client.purchase_ship(
            waypoint_symbol=waypoint_symbol, ship_type=ship_type
        )
        ship_purchase = cast(ShipPurchase, ship_purchase_response.data)
        print_as_table(
            title=f"Ship purchased - {ship_type}",
            data=[ship_purchase],
            console=self.console,
        )

    def buy(self, call_sign: str, symbol: str, units: int) -> None:
        sale_response = self.client.buy(call_sign=call_sign, symbol=symbol, units=units)
        purchase = cast(PurchaseOrSale, sale_response.data)
        print_as_table(
            title=f"Buy success - {call_sign} for {units} of {symbol}",
            data=[purchase],
            console=self.console,
        )

    def sell(self, call_sign: str, symbol: str, units: int) -> None:
        sale_response = self.client.sell(
            call_sign=call_sign, symbol=symbol, units=units
        )
        sale = cast(PurchaseOrSale, sale_response.data)
        print_as_table(
            title=f"Sale success - {call_sign} for {units} of {symbol}",
            data=[sale],
            console=self.console,
        )

    def systems(self) -> None:
        systems_response = self.client.systems()
        systems: List[System] = cast(List[System], systems_response.data)
        print_as_table(title="Systems", data=systems, console=self.console)

    def ships(self, silent: bool = False) -> None:
        ships_response = self.client.ships()
        ships: List[Ship] = cast(List[Ship], ships_response.data)
        if not silent:
            print_as_table(title="Ships", data=ships, console=self.console)
        save_client_ships(engine=self.dao.engine, ships=ships)

    def ship(self, call_sign: str) -> None:
        ship_response = self.client.ship(call_sign=call_sign)
        ship: Ship = cast(Ship, ship_response.data)
        print_as_table(title=f"Ship - {call_sign}", data=[ship], console=self.console)
        save_client_ships(engine=self.dao.engine, ships=[ship])

    def system(self, symbol: str) -> None:
        system_response = self.client.system(symbol=symbol)
        system = cast(System, system_response.data)
        print_as_table(title="System", data=[system], console=self.console)

    def waypoints(self, system_symbol: str) -> None:
        waypoints_response = self.client.waypoints(system_symbol=system_symbol)
        waypoints = cast(List[Waypoint], waypoints_response.data)
        print_as_table(title="Waypoints", data=waypoints, console=self.console)
        save_client_waypoints(engine=self.dao.engine, waypoints=waypoints)

    def waypoint(self, system_symbol: str, waypoint_symbol: str) -> None:
        waypoint_response = self.client.waypoint(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        )
        waypoint = cast(Waypoint, waypoint_response.data)
        print_as_table(
            title=f"Waypoint - {waypoint_symbol}", data=[waypoint], console=self.console
        )

    def navigate(self, call_sign: str, waypoint_symbol: str) -> None:
        navigate_response = self.client.navigate(
            call_sign=call_sign, waypoint_symbol=waypoint_symbol
        )
        navigate = cast(Navigation, navigate_response.data)
        print_as_table(
            title=f"Navigation - {call_sign}", data=[navigate], console=self.console
        )

    def miner_loop(self, call_sign: str, repeat: bool) -> None:
        if not self.api_key:
            raise TraderClientException("No API key present to proceed")
        miner = SimpleMiner(api_key=self.api_key, call_sign=call_sign, repeat=repeat)
        miner.run_loop()

    def trader_loop(self, call_sign: str, repeat: bool) -> None:
        if not self.api_key:
            raise TraderClientException("No API key present to proceed")
        trader = SimpleTrader(api_key=self.api_key, call_sign=call_sign, repeat=repeat)
        trader.run_loop()

    def explorer_loop(self, call_sign: str, repeat: bool) -> None:
        if not self.api_key:
            raise TraderClientException("No API key present to proceed")
        explorer = SimpleExplorer(
            api_key=self.api_key, call_sign=call_sign, repeat=repeat
        )
        explorer.run_loop()

    def leader_loop(self, call_sign: str, repeat: bool) -> None:
        if not self.api_key:
            raise TraderClientException("No API key present to proceed")
        leader = Leader(api_key=self.api_key, call_sign=call_sign, repeat=repeat)
        leader.run_loop()

    def fleet_loop(self) -> None:
        if not self.api_key:
            raise TraderClientException("No API key present to proceed")
        self.ships(silent=True)
        ships: Sequence[ShipDAO] = []
        with Session(self.dao.engine) as session:
            ships = session.exec(select(ShipDAO)).all()

        fleet = Fleet(api_key=self.api_key, ships=ships)
        fleet.run_loop()

    def fleet_summary(self, call_sign: Optional[str] = None, limit: int = 1) -> None:
        self.ships(silent=True)
        fleet: List[FleetSummaryRow] = []
        ship_events = get_ship_events(
            engine=self.dao.engine, call_sign=call_sign, limit=limit
        )
        for ship, ship_event in ship_events:
            logic, activity = ship_event.event_name.split(".")
            fleet.append(
                FleetSummaryRow(
                    ship_id=str(ship.id),
                    frame_name=ship.frame_name,
                    waypoint_symbol=ship.waypoint_symbol,
                    logic=logic.replace("-", " "),
                    activity=activity,
                    duration=ship_event.duration,
                    credits_earned=ship_event.credits_earned,
                    credits_spent=ship_event.credits_spent,
                    record_date=ship_event.created_at,
                )
            )
        # include freshly bought ships that haven't been evented yet
        ships: Sequence[ShipDAO] = []
        if call_sign:
            ship = get_ship(engine=self.dao.engine, call_sign=call_sign)
            if ship:
                ships = [ship]
        else:
            ships = get_ships(engine=self.dao.engine)
        for ship in ships:
            if ship.id not in [fleet_member.ship_id for fleet_member in fleet]:
                fleet.append(
                    FleetSummaryRow(
                        ship_id=str(ship.id),
                        frame_name=ship.frame_name,
                        waypoint_symbol=ship.waypoint_symbol,
                    )
                )
        if call_sign:
            title = f"Ship Summary - {call_sign}"
        else:
            title = "Fleet Summary"
        print_as_table(title=title, data=fleet, console=self.console)

    def agent_history(self):
        self.agent(silent=True)
        agent_histories: List[AgentHistoryRow] = []
        agent_histories_data = get_agent_histories(engine=self.dao.engine)
        for agent_history in agent_histories_data:
            agent_histories.append(
                AgentHistoryRow(
                    agent_symbol=agent_history.agent_symbol,
                    ship_count=agent_history.ship_count,
                    in_system_count=agent_history.in_system_count,
                    credits=agent_history.credits,
                    record_date=agent_history.created_at,
                )
            )
        print_as_table(
            title="Agent History", data=agent_histories, console=self.console
        )

    def reset(self):
        logger.warning("Resetting all local data!")
