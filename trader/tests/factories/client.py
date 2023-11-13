"""
Mocking all the client models for individual utilities and possible one-off functions

Mocking all payloads for rest calls
"""
from polyfactory.factories import DataclassFactory

from trader.client.agent import Agent
from trader.client.cargo import Cargo
from trader.client.contract import Contract
from trader.client.cooldown import Cooldown
from trader.client.extraction import Extraction
from trader.client.faction import Faction
from trader.client.fuel import Refuel
from trader.client.market import Market, PurchaseOrSale
from trader.client.navigation import Dock, NavigationAndFuel, Orbit
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
from trader.client.ship import Ship
from trader.client.ship_purchase import ShipPurchase
from trader.client.shipyard import Shipyard
from trader.client.status import LeaderBoard, ServerReset
from trader.client.system import System
from trader.client.waypoint import Waypoint


class AgentFactory(DataclassFactory[Agent]):
    __model__ = Agent


class CargoFactory(DataclassFactory[Cargo]):
    __model__ = Cargo


class ContractFactory(DataclassFactory[Contract]):
    __model__ = Contract


class CooldownFactory(DataclassFactory[Cooldown]):
    __model__ = Cooldown


class ExtractionFactory(DataclassFactory[Extraction]):
    __model__ = Extraction


class FactionFactory(DataclassFactory[Faction]):
    __model__ = Faction


class RefuelFactory(DataclassFactory[Refuel]):
    __model__ = Refuel


class MarketFactory(DataclassFactory[Market]):
    __model__ = Market


class SaleFactory(DataclassFactory[PurchaseOrSale]):
    __model__ = PurchaseOrSale


class DockFactory(DataclassFactory[Dock]):
    __model__ = Dock


class OrbitFactory(DataclassFactory[Orbit]):
    __model__ = Orbit


class ShipFactory(DataclassFactory[Ship]):
    __model__ = Ship


class NavigationAndFuelFactory(DataclassFactory[NavigationAndFuel]):
    __model__ = NavigationAndFuel


class ShipPurchaseFactory(DataclassFactory[ShipPurchase]):
    __model__ = ShipPurchase


class ShipyardFactory(DataclassFactory[Shipyard]):
    __model__ = Shipyard


class LeaderBoardFactory(DataclassFactory[LeaderBoard]):
    __model__ = LeaderBoard


class ServerResetFactory(DataclassFactory[ServerReset]):
    __model__ = ServerReset


class SystemFactory(DataclassFactory[System]):
    __model__ = System


class WaypointFactory(DataclassFactory[Waypoint]):
    __model__ = Waypoint


class AgentPayloadFactory(DataclassFactory[AgentPayload]):
    __model__ = AgentPayload


class AgentsPayloadFactory(DataclassFactory[AgentsPayload]):
    __model__ = AgentsPayload


class CargoPayloadFactory(DataclassFactory[CargoPayload]):
    __model__ = CargoPayload


class CommonPayloadFactory(DataclassFactory[CommonPayloadFields]):
    __model__ = CommonPayloadFields


class ContractsPayloadFactory(DataclassFactory[ContractsPayload]):
    __model__ = ContractsPayload


class CooldownPayloadFactory(DataclassFactory[CooldownPayload]):
    __model__ = CooldownPayload


class DockPayloadFactory(DataclassFactory[DockPayload]):
    __model__ = DockPayload


class ExtractPayloadFactory(DataclassFactory[ExtractPayload]):
    __model__ = ExtractPayload


class MarketPayloadFactory(DataclassFactory[MarketPayload]):
    __model__ = MarketPayload


class NavigationPayloadFactory(DataclassFactory[NavigationPayload]):
    __model__ = NavigationPayload


class OrbitPayloadFactory(DataclassFactory[OrbitPayload]):
    __model__ = OrbitPayload


class RefuelPayloadFactory(DataclassFactory[RefuelPayload]):
    __model__ = RefuelPayload


class RegistrationResponsePayloadFactory(DataclassFactory[RegistrationResponsePayload]):
    __model__ = RegistrationResponsePayload


class PurchaseOrSalePayloadFactory(DataclassFactory[PurchaseOrSalePayload]):
    __model__ = PurchaseOrSalePayload


class ShipPayloadFactory(DataclassFactory[ShipPayload]):
    __model__ = ShipPayload


class ShipPurchasePayloadFactory(DataclassFactory[ShipPurchasePayload]):
    __model__ = ShipPurchasePayload


class ShipsPayloadFactory(DataclassFactory[ShipsPayload]):
    __model__ = ShipsPayload


class ShipyardPayloadFactory(DataclassFactory[ShipyardPayload]):
    __model__ = ShipyardPayload


class StatusPayloadFactory(DataclassFactory[StatusPayload]):
    __model__ = StatusPayload


class SystemPayloadFactory(DataclassFactory[SystemPayload]):
    __model__ = SystemPayload


class SystemsPayloadFactory(DataclassFactory[SystemsPayload]):
    __model__ = SystemsPayload


class WaypointPayloadFactory(DataclassFactory[WaypointPayload]):
    __model__ = WaypointPayload


class WaypointsPayloadFactory(DataclassFactory[WaypointsPayload]):
    __model__ = WaypointsPayload
