from dataclasses import dataclass
from math import dist
from typing import Any, Dict, List, Literal, Optional, cast

import pandas as pd
from dataclass_wizard import JSONWizard

from trader.dao.markets import MarketTradeGood
from trader.dao.waypoints import Waypoint
from trader.roles.navigator.geometry import (
    generate_graph_from_waypoints_means_shift_clustering,
)

MINIMUM_PROFIT_TO_TRADE = 0.05


@dataclass
class ArbitrageOpportunityData:
    """
    This dataclass exists as the common fieldset for both serializable and
    unserialzable data
    """

    purchase_waypoint_symbol: str
    purchase_supply: str
    purchase_price: int
    sell_waypoint_symbol: str
    sell_supply: str
    sell_price: int
    trade_good_symbol: str
    purchase_system_symbol: Optional[str] = None
    sell_system_symbol: Optional[str] = None
    profit: Optional[int] = None
    percent_profit: Optional[float] = None


@dataclass
class ArbitrageOpportunitySerializable(ArbitrageOpportunityData, JSONWizard):
    """
    This dataclass exists as an intermediary to feed in post processed
    data to the below final class. This is because the final class contains
    SQL models as clean return objects but this one is used in dataframes for
    serialization
    """

    class _(JSONWizard.Meta):
        key_transform_with_dump = "SNAKE"


@dataclass(kw_only=True)
class ArbitrageOpportunity(ArbitrageOpportunityData):
    purchase_waypoint: Waypoint
    sell_waypoint: Waypoint


def generate_arbitrage_opportunities(
    market_trade_goods: List[MarketTradeGood],
    waypoints: List[Waypoint],
    limit: int = 10,
    sort_field: Literal["profit", "percent_profit"] = "profit",
) -> List[ArbitrageOpportunity]:
    """
    This will, for a given list of trade goods across multiple waypoints,
    look for the pairing of highest and lowest sell and purchase prices.

    It will return a limit (default: 10) of possible arbitrage opportunities.
    """
    arbitrage_opportunities: List[ArbitrageOpportunitySerializable] = []
    pd_goods = pd.DataFrame([t.dict() for t in market_trade_goods])
    good_names = pd_goods["symbol"].unique()
    for good_name in good_names:
        good_rows: Any = pd_goods[pd_goods["symbol"] == good_name]
        lowest_purchase_price_loc = good_rows["purchase_price"].idxmin()
        highest_sale_price_loc = good_rows["sell_price"].idxmax()
        purchase_row = good_rows.loc[lowest_purchase_price_loc]
        sale_row = good_rows.loc[highest_sale_price_loc]
        # filter to within waypoints specified
        arbitrage_opportunities.append(
            ArbitrageOpportunitySerializable(
                purchase_waypoint_symbol=purchase_row.waypoint_symbol,
                purchase_price=purchase_row.purchase_price,
                purchase_supply=purchase_row.supply,
                sell_waypoint_symbol=sale_row.waypoint_symbol,
                sell_price=sale_row.sell_price,
                sell_supply=sale_row.supply,
                trade_good_symbol=good_name,
            )
        )

    # compute profit and ratio, and spit it out for determination
    arbitrage_data = pd.DataFrame([t.to_dict() for t in arbitrage_opportunities])
    arbitrage_data["profit"] = arbitrage_data["sell_price"].astype(
        int
    ) - arbitrage_data["purchase_price"].astype(int)
    arbitrage_data["percent_profit"] = arbitrage_data["profit"] / arbitrage_data[
        "purchase_price"
    ].astype(int)

    # Exclude non-profitable trades by profit margin (they could swing and end up
    # leaving us bagholders)
    arbitrage_data["percent_profit"] = arbitrage_data[
        arbitrage_data["percent_profit"] > MINIMUM_PROFIT_TO_TRADE
    ]["percent_profit"]
    arbitrage_data.dropna()

    most_profitable_trades = arbitrage_data.sort_values(sort_field, ascending=False)
    arbitrage_opportunities = [
        ArbitrageOpportunitySerializable.from_dict(trade.to_dict())
        for _, trade in most_profitable_trades.head(limit).iterrows()
    ]
    arbitrage_opportunities_with_waypoints = []
    for arbitrage_opportunity in arbitrage_opportunities:
        sell_waypoint = next(
            filter(
                lambda wp: wp.symbol == arbitrage_opportunity.sell_waypoint_symbol,
                waypoints,
            )
        )
        buy_waypoint = next(
            filter(
                lambda wp: wp.symbol == arbitrage_opportunity.purchase_waypoint_symbol,
                waypoints,
            )
        )
        arbitrage_opportunities_with_waypoints.append(
            ArbitrageOpportunity(
                **arbitrage_opportunity.to_dict(),
                purchase_waypoint=buy_waypoint,
                sell_waypoint=sell_waypoint
            )
        )
    return arbitrage_opportunities_with_waypoints


def find_profitable_trades_in_system(
    trade_goods: List[MarketTradeGood],
    waypoints: List[Waypoint],
    limit: int = 10,
    prefer_within_cluster: Optional[bool] = True,
) -> Dict[float, ArbitrageOpportunity]:
    arbitrage_opportunities = generate_arbitrage_opportunities(
        market_trade_goods=trade_goods,
        limit=limit,
        waypoints=waypoints,
    )
    graph = generate_graph_from_waypoints_means_shift_clustering(waypoints=waypoints)

    profit_to_opportunity: Dict[float, ArbitrageOpportunity] = {}

    for arbitrage_opportunity in arbitrage_opportunities:
        distance = dist(
            [
                arbitrage_opportunity.purchase_waypoint.x,
                arbitrage_opportunity.purchase_waypoint.y,
            ],
            [
                arbitrage_opportunity.sell_waypoint.x,
                arbitrage_opportunity.sell_waypoint.y,
            ],
        )
        if distance == 0.0:
            continue

        profit_to_distance_ratio = cast(int, arbitrage_opportunity.profit) / distance

        if prefer_within_cluster:
            sell_wp_cluster = next(
                filter(
                    lambda cluster: arbitrage_opportunity.sell_waypoint.symbol
                    in cluster[1]["cluster_waypoints_symbols"],
                    list(graph.nodes(data=True)),
                )
            )
            buy_wp_cluster = next(
                filter(
                    lambda cluster: arbitrage_opportunity.purchase_waypoint.symbol
                    in cluster[1]["cluster_waypoints_symbols"],
                    list(graph.nodes(data=True)),
                )
            )
            if sell_wp_cluster[0] == buy_wp_cluster[0]:
                profit_to_opportunity[profit_to_distance_ratio] = arbitrage_opportunity
        else:
            profit_to_opportunity[profit_to_distance_ratio] = arbitrage_opportunity
    return profit_to_opportunity


def find_most_profitable_trade_in_system(
    maximum_purchase_price: int | float,
    trade_goods: List[MarketTradeGood],
    waypoints: List[Waypoint],
    limit: int = 10,
    prefer_within_cluster: Optional[bool] = True,
) -> Optional[ArbitrageOpportunity]:
    """
    Evaluate, for a list of trade goods and waypoints, if we can just dump everything
    into a singular optimal possible trade
    """
    profit_to_opportunity = find_profitable_trades_in_system(
        trade_goods=trade_goods,
        waypoints=waypoints,
        limit=limit,
        prefer_within_cluster=prefer_within_cluster,
    )
    most_profitable_trades_within_systems = list(
        reversed(sorted(profit_to_opportunity.keys()))
    )
    most_profitable_trade = None
    for profitable_trade in most_profitable_trades_within_systems:
        if (
            profit_to_opportunity[profitable_trade].purchase_price
            <= maximum_purchase_price
        ):
            most_profitable_trade = profit_to_opportunity[profitable_trade]
            break

    return most_profitable_trade
