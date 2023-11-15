from datetime import UTC, datetime
from math import dist
from time import sleep
from typing import List, Optional

from loguru import logger
from sqlmodel import Session, select

from trader.client.agent import Agent
from trader.client.client import Client
from trader.client.market import Exchange
from trader.client.navigation import NavigationRequestPatch
from trader.client.ship import Ship
from trader.client.waypoint import Waypoint
from trader.dao.dao import DAO
from trader.dao.markets import MarketExchange, save_client_market
from trader.dao.ship_events import ShipEvent
from trader.dao.ships import save_client_ships
from trader.dao.shipyards import save_client_shipyard
from trader.dao.waypoints import Waypoint as WaypointDAO
from trader.dao.waypoints import get_waypoints_by_system_symbol, save_client_waypoints
from trader.exceptions import TraderClientException, TraderException
from trader.roles.navigator.fuel import FUEL_COST_MULTIPLIER

DEFAULT_ACTIONS_TIMEOUT = 5
MINIMUM_FUEL_PERCENTAGE = 0.25


class Common:
    agent: Agent
    client: Client
    dao: DAO
    ship: Ship
    # metrics
    credits_earned: int = 0
    credits_spent: int = 0
    time_started: datetime
    # other
    base_priority: int = 0

    def __init__(self, api_key: str, base_priority: int, call_sign: str):
        self.base_priority = base_priority
        self.client = Client(api_key=api_key, base_priority=self.base_priority)
        self.dao = DAO()
        self.time_started = datetime.now(UTC)
        self._hydrate_ship_and_agent(call_sign=call_sign)

    def _hydrate_ship_and_agent(self, call_sign: str):
        ship = self.client.ship(call_sign=call_sign).data
        if not ship:
            raise TraderClientException(
                "Unable to instantiate common client as ship payload was empty!"
            )
        self.ship = ship

        agent = self.client.agent().data
        if not agent:
            raise TraderClientException(
                "Unable to instantiate common client as agent payload was empty!"
            )
        self.agent = agent

    def __navigate_to_waypoint(self, waypoint_symbol: str, system_symbol: str):
        """
        To be used with extreme care to avoid infinite loops as nearly everything requires
        navigation. This is mean to be used specifically with refueling and refueling
        encapsulated functions. Avoid using this without refueling!

        In almost all cases you will want to use refuel_and_navigate_to_waypoint
        """
        try:
            self.wait()
            self.set_flight_mode_for_fuel_and_frame(
                waypoint_symbol=waypoint_symbol, system_symbol=system_symbol
            )
            self.client.orbit(call_sign=self.ship.symbol)

            navigation_result = self.client.navigate(
                self.ship.symbol, waypoint_symbol=waypoint_symbol
            )
            if (
                navigation_result.data
                and navigation_result.data.nav
                and navigation_result.data.nav.status == "IN_TRANSIT"
            ):
                time_to_wait = (
                    datetime.fromisoformat(navigation_result.data.nav.route.arrival)
                    - datetime.now(UTC)
                ).seconds + 1
                logger.info(
                    f"Waiting for ship {self.ship.symbol} to arrive at waypoint "
                    f"{waypoint_symbol} for {time_to_wait} second(s)"
                )
                sleep(time_to_wait)
        except TraderException as e:
            if "Ship is currently in-transit" in e.message:
                self.wait_for_ship_to_arrive_at_destination()
            elif "is currently located at the destination" not in e.message:
                # reraise if not currently at desired location, as this is possible
                raise

    def reset_metrics(self):
        self.credits_earned = 0
        self.credits_spent = 0
        self.time_started = datetime.now(UTC)

    def add_to_credits_earned(self, credits: int):
        self.credits_earned += credits

    def add_to_credits_spent(self, credits: int):
        self.credits_spent += credits

    def fetch_waypoints_possible_for_ship(self) -> List[Waypoint] | List[WaypointDAO]:
        waypoints = get_waypoints_by_system_symbol(
            engine=self.dao.engine, system_symbol=self.ship.nav.system_symbol
        )
        if not waypoints:
            raw_locations_from_client = self.client.waypoints(
                self.ship.nav.system_symbol
            ).data
            if not raw_locations_from_client:
                raise TraderException("No waypoints found to find locations to mine!")
            else:
                save_client_waypoints(
                    engine=self.dao.engine, waypoints=raw_locations_from_client
                )
                waypoints = raw_locations_from_client
        return waypoints

    def find_closest_market_location_with_goods(
        self, goods: List[str] = []
    ) -> Waypoint:
        locations = {}
        # check if waypoints exist in db for system, if so we can just use that as there's no need to regrok
        waypoints = self.fetch_waypoints_possible_for_ship()
        for waypoint in waypoints:
            if "MARKETPLACE" not in [trait.symbol for trait in waypoint.traits]:
                continue
            # check if exchange aleady in db / cache first, otherwise go to retrieve it from API and hydrate
            market_exchanges: List[MarketExchange] | List[Exchange] = []
            with Session(self.dao.engine) as session:
                market_exchanges = session.exec(
                    select(MarketExchange).where(
                        MarketExchange.waypoint_symbol == waypoint.symbol
                    )
                ).all()
            if not market_exchanges:
                market_data = self.client.market(
                    system_symbol=waypoint.system_symbol,
                    waypoint_symbol=waypoint.symbol,
                )
                if market_data.data:
                    save_client_market(
                        engine=self.dao.engine,
                        market=market_data.data,
                        system_symbol=waypoint.system_symbol,
                    )
                    market_exchanges = market_data.data.exchange

            if not set(goods).issubset([entry.symbol for entry in market_exchanges]):
                continue
            distance_from_current_location = dist(
                [
                    self.ship.nav.route.destination.x,
                    self.ship.nav.route.destination.y,
                ],
                [waypoint.x, waypoint.y],
            )
            locations[distance_from_current_location] = waypoint
        return locations[min(locations.keys())]

    def set_flight_mode_for_fuel_and_frame(
        self, waypoint_symbol: str, system_symbol: str
    ):
        if self.ship.frame.name == "Probe":
            logger.info(
                f"Is probe {self.ship.symbol}, so no need to change flight mode"
            )
            # probes have no impact if you change their flight mode as per fix week 11/3
            return

        waypoint = self.client.waypoint(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        ).data
        if waypoint:
            distance = dist(
                [waypoint.x, waypoint.y],
                [self.ship.nav.route.destination.x, self.ship.nav.route.destination.y],
            )
            flight_mode_to_use = "CRUISE"
            fuel_cost = FUEL_COST_MULTIPLIER[flight_mode_to_use](int(distance))
            if (
                fuel_cost > 0.8 * self.ship.fuel.current
            ):  # be a little conservative about saved fuel
                # if too expensive, rely on drift
                flight_mode_to_use = "DRIFT"

            logger.info(
                f"Setting ship {self.ship.symbol} flight mode to {flight_mode_to_use} because of fuel cost ({fuel_cost}) "
                f"vs. current fuel ({self.ship.fuel.current})"
            )
            self.client.set_flight_mode(
                call_sign=self.ship.symbol,
                data=NavigationRequestPatch(flight_mode=flight_mode_to_use),
            )

    def refuel_ship(self):
        logger.info(f"Ship {self.ship.symbol} starting to navigate to refuel")
        try:
            self.client.orbit(
                call_sign=self.ship.symbol
            )  # ensure that the ship is always in a position to continue (if previously orphaned by other activity)
            closest_market_location = self.find_closest_market_location_with_goods(
                goods=["FUEL"]
            )
            self.__navigate_to_waypoint(
                waypoint_symbol=closest_market_location.symbol,
                system_symbol=closest_market_location.system_symbol,
            )
            self.client.dock(call_sign=self.ship.symbol)
            self.refresh_market_data(
                system_symbol=closest_market_location.system_symbol,
                waypoint_symbol=closest_market_location.symbol,
            )
            refuel_response = self.client.refuel(call_sign=self.ship.symbol)
            if refuel_response.data:
                self.add_to_credits_spent(
                    credits=refuel_response.data.transaction.total_price
                )
            self.reload_ship()  # keep up to date fuel data
            self.client.orbit(call_sign=self.ship.symbol)
        except TraderException as e:
            if "Ship is currently in-transit" in e.message:
                self.wait_for_ship_to_arrive_at_destination()
                return self.refuel_ship()
            raise

    def reload_ship(self):
        ship = self.client.ship(call_sign=self.ship.symbol).data
        if ship:
            save_client_ships(engine=self.dao.engine, ships=[ship])
            self.ship = ship
        agent = self.client.agent().data
        if agent:
            self.agent = agent

    def wait(self):
        attempts = 0
        while True:
            if attempts > 3:
                break
            try:
                # check if in transit
                self.reload_ship()
                if self.ship.nav.status == "IN_TRANSIT":
                    self.wait_for_ship_to_arrive_at_destination()
                else:
                    # otherwise verify there's no active cooldowns
                    cooldown = self.client.cooldown(self.ship.symbol)
                    if cooldown.data and cooldown.data.remaining_seconds != 0:
                        logger.info(
                            f"Ship {self.ship.symbol} waiting for cooldown for {cooldown.data.remaining_seconds} seconds"
                        )
                        sleep(cooldown.data.remaining_seconds)
                    else:
                        sleep(DEFAULT_ACTIONS_TIMEOUT)
                    attempts += 1
            except TraderException as e:
                if "Empty response" in e.message:
                    break
                raise
        self.reload_ship()

    def wait_for_ship_to_arrive_at_destination(self) -> None:
        self.reload_ship()
        time_to_wait = (
            datetime.fromisoformat(self.ship.nav.route.arrival) - datetime.now(UTC)
        ).seconds + 1
        logger.warning(
            f"Waiting for ship {self.ship.symbol} to arrive at already "
            f"bound destination {self.ship.nav.route.destination.symbol} for {time_to_wait} second(s)"
        )
        sleep(time_to_wait)

    def refresh_market_data(self, system_symbol: str, waypoint_symbol: str) -> None:
        market = self.client.market(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        ).data
        if market:
            save_client_market(
                engine=self.dao.engine,
                market=market,
                system_symbol=system_symbol,
            )

    def refresh_shipyard_data(self, system_symbol: str, waypoint_symbol: str) -> None:
        shipyard = self.client.shipyard(
            system_symbol=system_symbol, waypoint_symbol=waypoint_symbol
        ).data
        if shipyard:
            save_client_shipyard(
                engine=self.dao.engine,
                shipyard=shipyard,
                system_symbol=system_symbol,
            )

    def refuel_and_navigate_to_waypoint(self, waypoint_symbol: str, system_symbol: str):
        logger.info(
            f"Ship {self.ship.symbol} refueling first and then navigating to waypoint {waypoint_symbol} and waiting"
        )
        if (
            self.ship.fuel.current <= self.ship.fuel.capacity * MINIMUM_FUEL_PERCENTAGE
            and self.ship.frame.name != "Probe"
        ):
            # probes do not need to refuel
            self.refuel_ship()
            logger.info(
                f"Ship {self.ship.symbol} completed refueling, heading to {waypoint_symbol} now"
            )
        logger.info(
            f"Ship {self.ship.symbol} completed refueling, now navigating to waypoint {waypoint_symbol} and waiting"
        )
        # warning - ensure this is the only usage of navigate below, as we will want to always
        # refuel to avoid drifting (too slow)
        self.__navigate_to_waypoint(
            waypoint_symbol=waypoint_symbol, system_symbol=system_symbol
        )

    def log_update(self, source: str, source_emoji: str, message: str):
        logger.info(f"{source_emoji} - {source} - {message}")

    def save_to_audit_table(
        self,
        event_name: str,
        duration: int,
        ship_id: str,
        system_symbol: Optional[str],
        waypoint_symbol: Optional[str],
        credits_earned: Optional[int],
        credits_spent: Optional[int],
    ):
        with Session(self.dao.engine) as session:
            session.add(
                ShipEvent(
                    event_name=event_name,
                    duration=duration,
                    ship_id=ship_id,
                    system_symbol=system_symbol,
                    waypoint_symbol=waypoint_symbol,
                    credits_earned=credits_earned,
                    credits_spent=credits_spent,
                    created_at=datetime.now(UTC),
                )
            )
            session.commit()
