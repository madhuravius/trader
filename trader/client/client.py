from typing import Any, Dict, List, Optional, Type, cast

import httpx
from loguru import logger

from trader.cache import Cache
from trader.client.cargo import SellCargoRequest
from trader.client.navigation import NavigationRequestData
from trader.client.payload import (
    AgentPayload,
    AgentsPayload,
    CargoPayload,
    CommonPayloadFields,
    ContractsPayload,
    CooldownPayload,
    DockPayload,
    ExtractPayload,
    MarketPayload,
    NavigationPayload,
    OrbitPayload,
    PayloadTypes,
    RefuelPayload,
    RegistrationResponsePayload,
    SalePayload,
    ShipPayload,
    ShipsPayload,
    SystemPayload,
    SystemsPayload,
    WaypointsPayload,
)
from trader.client.registration import RegistrationRequestData
from trader.client.request import ClientRequest
from trader.exceptions import TraderException
from trader.queue import Queue
from trader.util.singleton import Singleton

BASE_URL = "https://api.spacetraders.io/v2"


class Client(metaclass=Singleton):
    api_key: Optional[str]
    bearer: str
    cache: Cache
    queue: Queue

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key
        self.bearer = f"Bearer {self.api_key}".replace("\n", "")
        self.cache = Cache()
        self.queue = Queue()

    def ensure_api_key(self):
        if not self.api_key:
            raise TraderException("No API key found in path, error!")

    def ensure_success(self, response: CommonPayloadFields):
        if response.error and response.error.code and response.error.code >= 400:
            logger.error(
                f"Error {response.error.code} in handling request: {response.error.message}"
            )
            raise TraderException(
                response.error.message or f"Error with code: {response.error.code}"
            )

    def ensure_singular_payload(
        self, response_content: bytes, data_type: Type[PayloadTypes]
    ) -> PayloadTypes:
        """
        This function ensures a single payload because dataclass_wizard will often generate array results
        """
        if not response_content:
            raise TraderException(message="Empty response")

        try:
            response = data_type.from_json(response_content)
        except Exception as e:
            logger.exception(e)
            raise e
        if isinstance(response, List):
            response = response[0]

        self.ensure_success(response)
        return response

    def conduct_request(
        self,
        url: str,
        method: str,
        check_cache: bool = True,
        data: Optional[Dict[str, Any]] = {},
        is_paged: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> httpx.Response:
        logger.debug(f"📤     {method}: {url}")

        params = {}
        if is_paged:
            params = {"limit": limit, "page": page}

        if check_cache:
            cached_response = self.cache.get_kv_cache(
                method=method, url=url, data=data, params=params
            )
            if cached_response:
                return cached_response

        arguments: Dict[str, Any] = {"url": url, "params": params}
        if self.api_key:
            arguments["headers"] = {"Authorization": self.bearer}
        if data:
            arguments["json"] = data

        if method == "POST":
            request = ClientRequest(function=httpx.post, arguments=arguments)
        else:
            request = ClientRequest(function=httpx.get, arguments=arguments)

        request_id = self.queue.enqueue(request=request, priority=1)
        response = self.queue.wait_for_response(request_id=request_id)

        if check_cache:
            self.cache.set_kv_cache(
                method=method, url=url, data=data, response=response, params=params
            )

        logger.debug(f"📨 {response.status_code} {method}: {url}")

        return response

    def register(self, data: RegistrationRequestData) -> RegistrationResponsePayload:
        response = self.conduct_request(
            data=data.to_dict(),
            url=f"{BASE_URL}/register",
            method="POST",
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=RegistrationResponsePayload
        )
        return cast(RegistrationResponsePayload, result)

    def agents(self) -> AgentsPayload:
        self.ensure_api_key()
        response = self.conduct_request(url=f"{BASE_URL}/agents", method="GET")

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=AgentsPayload
        )
        return cast(AgentsPayload, result)

    def agent(self) -> AgentPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/agent", method="GET", check_cache=False
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=AgentPayload
        )
        return cast(AgentPayload, result)

    def contracts(self) -> ContractsPayload:
        self.ensure_api_key()
        response = self.conduct_request(url=f"{BASE_URL}/my/contracts", method="GET")

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=ContractsPayload
        )
        return cast(ContractsPayload, result)

    def ships(self) -> ShipsPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships", method="GET", check_cache=False
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=ShipsPayload
        )
        return cast(ShipsPayload, result)

    def ship(self, call_sign: str) -> ShipPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}",
            method="GET",
            check_cache=False,
            is_paged=True,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=ShipPayload
        )
        return cast(ShipPayload, result)

    def system(self, symbol: str) -> SystemPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/systems/{symbol}", method="GET"
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=SystemPayload
        )
        return cast(SystemPayload, result)

    def systems(self) -> SystemsPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/systems", method="GET", is_paged=True
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=SystemsPayload
        )
        return cast(SystemsPayload, result)

    def waypoints(self, system_symbol: str) -> WaypointsPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints",
            method="GET",
            is_paged=True,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=WaypointsPayload
        )
        return cast(WaypointsPayload, result)

    def navigate(self, call_sign: str, waypoint_symbol: str) -> NavigationPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/navigate",
            method="POST",
            data=NavigationRequestData(waypoint_symbol=waypoint_symbol).to_dict(),
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=NavigationPayload
        )
        return cast(NavigationPayload, result)

    def orbit(self, call_sign: str) -> OrbitPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/orbit",
            method="POST",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=OrbitPayload
        )
        return cast(OrbitPayload, result)

    def dock(self, call_sign: str) -> DockPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/dock",
            method="POST",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=DockPayload
        )
        return cast(DockPayload, result)

    def cargo(self, call_sign: str) -> CargoPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/cargo",
            method="GET",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=CargoPayload
        )
        return cast(CargoPayload, result)

    def extract(self, call_sign: str) -> ExtractPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/extract",
            method="POST",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=ExtractPayload
        )
        return cast(ExtractPayload, result)

    def refuel(self, call_sign: str) -> RefuelPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/refuel",
            method="POST",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=RefuelPayload
        )
        return cast(RefuelPayload, result)

    def cooldown(self, call_sign: str) -> CooldownPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/cooldown",
            method="GET",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=CooldownPayload
        )
        return cast(CooldownPayload, result)

    def market(self, system_symbol: str, waypoint_symbol: str) -> MarketPayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints/{waypoint_symbol}/market",
            method="GET",
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=MarketPayload
        )
        return cast(MarketPayload, result)

    def sell(self, call_sign: str, symbol: str, units: int) -> SalePayload:
        self.ensure_api_key()
        response = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/sell",
            method="POST",
            data=SellCargoRequest(symbol=symbol, units=units).to_dict(),
            check_cache=False,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=SalePayload
        )
        return cast(SalePayload, result)
