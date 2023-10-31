from datetime import UTC, datetime
from time import sleep
from typing import List, Optional

from loguru import logger
from sqlmodel import Session

from trader.client.client import Client
from trader.client.ship import Ship
from trader.dao.dao import DAO
from trader.dao.ship_events import ShipEvent
from trader.exceptions import TraderException
from trader.util.geometry import compute_distance

DEFAULT_ACTIONS_TIMEOUT = 5


class Common:
    client: Client
    dao: DAO
    ship: Ship
    # metrics
    credits_earned: int = 0
    credits_spent: int = 0
    time_started: datetime

    def __init__(self, api_key: str, call_sign: str):
        self.client = Client(api_key=api_key)
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
            x1, y1 = (
                self.ship.nav.route.destination.x,
                self.ship.nav.route.destination.y,
            )
            x2, y2 = location.x, location.y
            distance_from_current_location = compute_distance(
                x1=x1, x2=x2, y1=y1, y2=y2
            )
            locations[distance_from_current_location] = location
        return locations[min(locations.keys())]

    def refuel_ship(self):
        logger.info(f"Ship {self.ship.symbol} starting to navigate to refuel")
        self.client.orbit(
            call_sign=self.ship.symbol
        )  # ensure that the ship is always in a position to continue (if previously orphaned by other activity)
        closest_market_location = self.find_closest_market_location_with_goods(
            goods=["FUEL"]
        )
        self.navigate_to_waypoint(waypoint_symbol=closest_market_location.symbol)
        self.client.dock(call_sign=self.ship.symbol)
        refuel_response = self.client.refuel(call_sign=self.ship.symbol)
        if refuel_response.data:
            self.add_to_credits_spent(
                credits=refuel_response.data.transaction.total_price
            )
        self.reload_ship()  # keep up to date fuel data
        self.client.orbit(call_sign=self.ship.symbol)

    def reload_ship(self):
        ship = self.client.ship(call_sign=self.ship.symbol).data
        if ship:
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

    def navigate_to_waypoint(self, waypoint_symbol: str):
        logger.info(
            f"Ship {self.ship.symbol} navigating to waypoint {waypoint_symbol} and waiting"
        )
        try:
            navigation_result = self.client.navigate(
                self.ship.symbol, waypoint_symbol=waypoint_symbol
            )
            if (
                navigation_result.data
                and navigation_result.data.nav.status == "IN_TRANSIT"
            ):
                time_to_wait = (
                    datetime.fromisoformat(navigation_result.data.nav.route.arrival)
                    - datetime.now(UTC)
                ).seconds + 1
                logger.info(
                    f"Waiting for ship {self.ship.symbol} to arrive at waypoint {waypoint_symbol} for {time_to_wait} second(s)"
                )
                sleep(time_to_wait)
        except TraderException as e:
            if "is currently located at the destination" not in e.message:
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
