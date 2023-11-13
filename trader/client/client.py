import os
from typing import Any, Dict, List, Literal, Optional, Type, cast
from uuid import uuid4

import httpx
from loguru import logger

from trader.client.cargo import CargoRequest
from trader.client.navigation import NavigationRequestData, NavigationRequestPatch
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
    PurchaseOrSalePayload,
    RefuelPayload,
    RegistrationResponsePayload,
    ShipPayload,
    ShipPurchasePayload,
    ShipsPayload,
    ShipyardPayload,
    StatusPayload,
    SystemPayload,
    SystemsPayload,
    WaypointPayload,
    WaypointsPayload,
)
from trader.client.registration import RegistrationRequestData
from trader.client.request import ClientRequest
from trader.client.request_cache import Cache
from trader.client.shipyard import ShipPurchaseRequestData
from trader.exceptions import TraderClientException
from trader.queues.request_queue import RequestQueue
from trader.util.singleton import Singleton

BASE_URL = "https://api.spacetraders.io/v2"


class CoreClient(metaclass=Singleton):
    """
    Intensive DAO and Cache heavy component of client. This portion is a singleton
    to avoid reinstantiation and is consistently referenced.
    """

    api_key: Optional[str]
    bearer: str
    cache: Cache

    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key
        self.bearer = f"Bearer {self.api_key}".replace("\n", "")
        self.cache = Cache()

    def ensure_api_key(self):
        if not self.api_key:
            raise TraderClientException("No API key found in path, error!")


class Client:
    """
    Lighter weight client wrapper that handles client calls systematically. The
    core client is a singleton as init'ing it is fairly heavy per call.
    """

    base_priority: int
    client_id: str
    core: CoreClient
    debug: bool
    request_queue: RequestQueue

    def __init__(
        self,
        api_key: Optional[str],
        base_priority: int = 0,
        disable_background_processes: bool = False,
    ) -> None:
        self.base_priority = base_priority
        self.client_id = str(uuid4())
        self.core_client = CoreClient(api_key=api_key)
        self.debug = "DEBUG" in os.environ
        self.request_queue = RequestQueue(
            client_id=self.client_id,
            disable_background_processes=disable_background_processes,
        )

    def set_base_priority(self, base_priority: int):
        self.base_priority = base_priority

    def ensure_success(self, response: CommonPayloadFields):
        if response.error and response.error.code and response.error.code >= 400:
            logger.error(
                f"Error {response.error.code} in handling request: {response.error.message}"
            )
            raise TraderClientException(
                response.error.message or f"Error with code: {response.error.code}"
            )

    def ensure_singular_payload(
        self,
        response_content: bytes,
        data_type: Type[PayloadTypes] | Type[StatusPayload],
    ) -> PayloadTypes | StatusPayload:
        """
        This function ensures a single payload because dataclass_wizard will often generate array results
        """
        if not response_content:
            raise TraderClientException(message="Empty response")

        try:
            response = data_type.from_json(response_content)
        except Exception as e:
            logger.exception(e)
            raise e
        if isinstance(response, List):
            response = response[0]

        self.ensure_success(response)
        if "REQUEST_DEBUG" in os.environ:
            logger.debug(response)
        return response

    def execute_single_request(
        self,
        url: str,
        method: Literal["GET", "POST", "PATCH"],
        cache_timeout: Optional[float] = None,
        check_cache: bool = True,
        data: Optional[Dict[str, Any]] = {},
        is_paged: bool = False,
        page: int = 1,
        added_priority: int = 0,
        limit: int = 20,
    ) -> httpx.Response:
        logger.debug(f"📤     {method}: {url}")

        params = {}
        if is_paged:
            params = {"limit": limit, "page": page}

        if check_cache:
            cached_response = self.core_client.cache.get_kv_cache(
                method=method, url=url, data=data, params=params
            )
            if cached_response:
                if self.debug:
                    logger.trace(cached_response.content)
                return cached_response

        arguments: Dict[str, Any] = {"url": url, "params": params}
        if self.core_client.api_key:
            arguments["headers"] = {"Authorization": self.core_client.bearer}
        if data:
            arguments["json"] = data

        if method == "POST":
            request = ClientRequest(function=httpx.post, arguments=arguments)
        elif method == "PATCH":
            request = ClientRequest(function=httpx.patch, arguments=arguments)
        else:
            request = ClientRequest(function=httpx.get, arguments=arguments)

        request_id = self.request_queue.enqueue(
            request=request, priority=self.base_priority + added_priority
        )
        response = self.request_queue.wait_for_response(request_id=request_id)

        if check_cache:
            cache_arguments = {
                "method": method,
                "url": url,
                "data": data,
                "response": response,
                "params": params,
            }
            if cache_timeout:
                cache_arguments["cache_timeout"] = cache_timeout
            self.core_client.cache.set_kv_cache(**cache_arguments)

        logger.debug(f"📨 {response.status_code} {method}: {url}")

        if self.debug:
            logger.trace(response.content)

        return response

    def conduct_request(
        self,
        url: str,
        method: Literal["GET", "POST", "PATCH"],
        data_type: Type[PayloadTypes | StatusPayload],
        cache_timeout: Optional[float] = None,
        check_cache: bool = True,
        data: Optional[Dict[str, Any]] = {},
        is_paged: bool = False,
        page: int = 1,
        requires_auth: bool = True,
        added_priority: int = 0,
        limit: int = 20,
    ) -> PayloadTypes | StatusPayload:
        if requires_auth:
            self.core_client.ensure_api_key()

        response = self.execute_single_request(
            url=url,
            method=method,
            cache_timeout=cache_timeout,
            check_cache=check_cache,
            data=data,
            is_paged=is_paged,
            page=page,
            added_priority=added_priority,
            limit=limit,
        )

        result = self.ensure_singular_payload(
            response_content=response.content, data_type=data_type
        )

        if type(result) == StatusPayload:
            return result

        result = cast(PayloadTypes, result)
        if is_paged and result.meta and type(result.data) == list:
            logger.info(
                f"Querying paged results for total {result.meta.total} entries."
            )
            accumulated_total = limit
            results: List[PayloadTypes] = cast(List[PayloadTypes], [result])
            while accumulated_total < result.meta.total:
                page += 1
                paged_result = cast(
                    PayloadTypes,
                    self.ensure_singular_payload(
                        response_content=self.execute_single_request(
                            url=url,
                            method=method,
                            cache_timeout=cache_timeout,
                            check_cache=check_cache,
                            data=data,
                            is_paged=is_paged,
                            page=page,
                            added_priority=added_priority,
                            limit=limit,
                        ).content,
                        data_type=data_type,
                    ),
                )
                results.append(paged_result)
                accumulated_total += limit
            for paged_result in results:
                if result.data and paged_result.data:
                    # below line is commented because
                    result.data = result.data + paged_result.data  # type: ignore

        return result

    def register(self, data: RegistrationRequestData) -> RegistrationResponsePayload:
        result = self.conduct_request(
            data=data.to_dict(),
            url=f"{BASE_URL}/register",
            method="POST",
            check_cache=False,
            data_type=RegistrationResponsePayload,
            requires_auth=False,
        )

        return cast(RegistrationResponsePayload, result)

    def status(self) -> StatusPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/",
            method="GET",
            check_cache=False,
            data_type=StatusPayload,
            requires_auth=False,
        )
        return cast(StatusPayload, result)

    def agents(self) -> AgentsPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/agents", method="GET", data_type=AgentsPayload
        )

        return cast(AgentsPayload, result)

    def agent(self) -> AgentPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/agent",
            method="GET",
            check_cache=False,
            data_type=AgentPayload,
        )
        return cast(AgentPayload, result)

    def contracts(self) -> ContractsPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/contracts", method="GET", data_type=ContractsPayload
        )
        return cast(ContractsPayload, result)

    def ships(self) -> ShipsPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships",
            method="GET",
            check_cache=False,
            data_type=ShipsPayload,
        )
        return cast(ShipsPayload, result)

    def ship(self, call_sign: str) -> ShipPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}",
            method="GET",
            check_cache=False,
            is_paged=True,
            data_type=ShipPayload,
        )
        return cast(ShipPayload, result)

    def system(self, symbol: str) -> SystemPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems/{symbol}", method="GET", data_type=SystemPayload
        )
        return cast(SystemPayload, result)

    def systems(self) -> SystemsPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems",
            method="GET",
            is_paged=True,
            data_type=SystemsPayload,
        )
        return cast(SystemsPayload, result)

    def waypoint(self, system_symbol: str, waypoint_symbol: str) -> WaypointPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints/{waypoint_symbol}",
            method="GET",
            data_type=WaypointPayload,
        )
        return cast(WaypointPayload, result)

    def waypoints(self, system_symbol: str) -> WaypointsPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints",
            method="GET",
            is_paged=True,
            data_type=WaypointsPayload,
        )
        return cast(WaypointsPayload, result)

    def navigate(self, call_sign: str, waypoint_symbol: str) -> NavigationPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/navigate",
            method="POST",
            data=NavigationRequestData(waypoint_symbol=waypoint_symbol).to_dict(),
            check_cache=False,
            data_type=NavigationPayload,
        )
        return cast(NavigationPayload, result)

    def orbit(self, call_sign: str) -> OrbitPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/orbit",
            method="POST",
            check_cache=False,
            data_type=OrbitPayload,
        )
        return cast(OrbitPayload, result)

    def dock(self, call_sign: str) -> DockPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/dock",
            method="POST",
            check_cache=False,
            data_type=DockPayload,
        )
        return cast(DockPayload, result)

    def cargo(self, call_sign: str) -> CargoPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/cargo",
            method="GET",
            check_cache=False,
            data_type=CargoPayload,
        )
        return cast(CargoPayload, result)

    def set_flight_mode(
        self, call_sign: str, data: NavigationRequestPatch
    ) -> CargoPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/nav",
            data=data.to_dict(),
            method="PATCH",
            check_cache=False,
            data_type=NavigationPayload,
        )
        return cast(CargoPayload, result)

    def extract(self, call_sign: str) -> ExtractPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/extract",
            method="POST",
            check_cache=False,
            data_type=ExtractPayload,
        )
        return cast(ExtractPayload, result)

    def refuel(self, call_sign: str) -> RefuelPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/refuel",
            method="POST",
            check_cache=False,
            data_type=RefuelPayload,
        )
        return cast(RefuelPayload, result)

    def cooldown(self, call_sign: str) -> CooldownPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/cooldown",
            method="GET",
            check_cache=False,
            data_type=CooldownPayload,
        )
        return cast(CooldownPayload, result)

    def market(self, system_symbol: str, waypoint_symbol: str) -> MarketPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints/{waypoint_symbol}/market",
            method="GET",
            check_cache=False,
            data_type=MarketPayload,
        )
        return cast(MarketPayload, result)

    def buy(self, call_sign: str, symbol: str, units: int) -> PurchaseOrSalePayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/purchase",
            method="POST",
            data=CargoRequest(symbol=symbol, units=units).to_dict(),
            check_cache=False,
            data_type=PurchaseOrSalePayload,
        )
        return cast(PurchaseOrSalePayload, result)

    def sell(self, call_sign: str, symbol: str, units: int) -> PurchaseOrSalePayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships/{call_sign}/sell",
            method="POST",
            data=CargoRequest(symbol=symbol, units=units).to_dict(),
            check_cache=False,
            data_type=PurchaseOrSalePayload,
        )
        return cast(PurchaseOrSalePayload, result)

    def shipyard(self, system_symbol: str, waypoint_symbol: str) -> ShipyardPayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/systems/{system_symbol}/waypoints/{waypoint_symbol}/shipyard",
            method="GET",
            check_cache=True,
            cache_timeout=120,  # drop cache every 120 seconds or so
            data_type=ShipyardPayload,
        )
        return cast(ShipyardPayload, result)

    def purchase_ship(
        self, ship_type: str, waypoint_symbol: str
    ) -> ShipPurchasePayload:
        result = self.conduct_request(
            url=f"{BASE_URL}/my/ships",
            method="POST",
            data=ShipPurchaseRequestData(
                ship_type=ship_type, waypoint_symbol=waypoint_symbol
            ).to_dict(),
            check_cache=False,
            cache_timeout=120,  # drop cache every 120 seconds or so
            data_type=ShipPurchasePayload,
        )
        return cast(ShipPurchasePayload, result)
