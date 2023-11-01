from datetime import UTC, datetime
from math import dist
from time import sleep
from typing import List, Optional

from loguru import logger
from sqlmodel import Session

from trader.client.client import Client
from trader.client.navigation import NavigationRequestPatch
from trader.client.ship import Ship
from trader.dao.dao import DAO
from trader.dao.markets import save_client_market
from trader.dao.ship_events import ShipEvent
from trader.dao.ships import save_client_ships
from trader.exceptions import TraderException

DEFAULT_ACTIONS_TIMEOUT = 5


class Common:
    client: Client
    dao: DAO
    ship: Ship
    # metrics
    credits_earned: int = 0
    credits_spent: int = 0
    time_started: datetime
    # other
    base_priority: int = 0

    def __init__(self, api_key: str, call_sign: str):
        self.client = Client(api_key=api_key, base_priority=self.base_priority)
        self.dao = DAO()
        self.time_started = datetime.utcnow()

        ship = self.client.ship(call_sign=call_sign).data
        if not ship:
            raise TraderException(
                "Unable to instantiate common client as ship payload was empty!"
            )

        self.ship = ship

    def reset_metrics(self):
        self.credits_earned = 0
        self.credits_spent = 0
        self.time_started = datetime.utcnow()

    def add_to_credits_earned(self, credits: int):
        self.credits_earned += credits

    def add_to_credits_spent(self, credits: int):
        self.credits_spent += credits

    def find_closest_market_location_with_goods(self, goods: List[str] = []):
        locations = {}
        raw_locations = self.client.waypoints(self.ship.nav.system_symbol)
        if not raw_locations.data:
            raise TraderException("No waypoints found to find locations to sell!")
        for location in raw_locations.data:
            if "MARKETPLACE" not in [trait.symbol for trait in location.traits]:
                continue
            # additionally query marketplace exchanges to see if goods are sold there
            market_data = self.client.market(
                system_symbol=location.system_symbol, waypoint_symbol=location.symbol
            )
            if market_data.data:
                if not set(goods).issubset(
                    [entry.symbol for entry in market_data.data.exchange]
                ):
                    continue
            distance_from_current_location = dist(
                [
                    self.ship.nav.route.destination.x,
                    self.ship.nav.route.destination.y,
                ],
                [location.x, location.y],
            )
            locations[distance_from_current_location] = location
        return locations[min(locations.keys())]

    def refuel_ship(self):
        logger.info(f"Ship {self.ship.symbol} starting to navigate to refuel")
        try:
            self.client.orbit(
                call_sign=self.ship.symbol
            )  # ensure that the ship is always in a position to continue (if previously orphaned by other activity)
            closest_market_location = self.find_closest_market_location_with_goods(
                goods=["FUEL"]
            )
            self.navigate_to_waypoint(waypoint_symbol=closest_market_location.symbol)
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
                self.refuel_ship()

    def reload_ship(self):
        ship = self.client.ship(call_sign=self.ship.symbol).data
        if ship:
            save_client_ships(engine=self.dao.engine, ships=[ship])
            self.ship = ship

    def wait(self):
        attempts = 0
        while True:
            if attempts > 3:
                break
            try:
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
        self.reload_ship()

    def wait_for_ship_to_arrive_at_destination(self) -> None:
        self.reload_ship()
        time_to_wait = (
            datetime.fromisoformat(self.ship.nav.route.arrival) - datetime.now(UTC)
        ).seconds + 1
        logger.warning(
            f"Waiting for ship {self.ship.symbol} to arrive at already"
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

    def navigate_to_waypoint(self, waypoint_symbol: str):
        logger.info(
            f"Ship {self.ship.symbol} navigating to waypoint {waypoint_symbol} and waiting"
        )
        try:
            if self.ship.frame == "Probe" and self.ship.nav.flight_mode != "BURN":
                logger.info(
                    f"Setting probe {self.ship.symbol} flight mode to burn as it is a probe (no fuel cost)"
                )
                self.client.set_flight_mode(
                    call_sign=self.ship.symbol,
                    data=NavigationRequestPatch(flight_mode="BURN"),
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
                    created_at=datetime.utcnow(),
                )
            )
            session.commit()
