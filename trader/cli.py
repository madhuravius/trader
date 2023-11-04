import os

import rich_click as click
from loguru import logger

from trader.client.navigation import FlightModes
from trader.exceptions import TraderException
from trader.main import Trader
from trader.print.print import print_alert

if "DEBUG" not in os.environ:
    logger.remove()
    logger.add("out.log")


class ClickCommandWrapper(click.Command):
    def invoke(self, ctx):
        try:
            super().invoke(ctx)
        except TraderException as e:
            print_alert(
                message=f"Error encountered: {e.message}", console=trader.console
            )
            close_cli(code=1)
        except Exception as e:
            close_cli(code=1)


def close_cli(code: int = 0):
    os._exit(code)


def trader_command(func=None, **kwargs):
    def decorator(func):
        return click.command(cls=ClickCommandWrapper, **kwargs)(func)

    return decorator if func is None else decorator(func)


trader = Trader()


@click.group()
@click.pass_context
def cli(ctx):
    """
    CLI wrapper around functionality for the SpaceTraders v2 API.

    This also contains more ambitious attempts to automate elements around the game.
    Source code can be found at mirror: https://github.com/madhuravius/trader

    Documentation for the API can be found here: https://docs.spacetraders.io/

    Logs should output to [yellow]out.log[/yellow]. Alternatively set the DEBUG=1 environment
    variable to see logs in stdout.
    """
    ctx.call_on_close(close_cli)


@trader_command()
def status():
    """
    Print out information about the backend. Ex: [yellow]cli.py status[/yellow]
    """
    trader.status()


@trader_command()
@click.argument("call_sign")
@click.argument("faction", type=click.Choice(["COSMIC"]))
def register(call_sign: str, faction: str):
    """
    Registers and stores token locally. Ex: [yellow]cli.py register CALL_SIGN FACTION[/yellow]
    """
    click.echo(f"Registering client for call_sign: {call_sign} ({faction})")
    trader.register(call_sign=call_sign, faction=faction)


@trader_command()
def agent():
    """
    Print out information for a given agent. Ex: [yellow]cli.py agent[/yellow]
    """
    trader.agent()


@trader_command()
def agents():
    """
    Print out information for all agents. Ex: [yellow]cli.py agents[/yellow]
    """
    trader.agents()


@trader_command()
def contracts():
    """
    Print out information for all active contracts. Ex: [yellow]cli.py contracts[/yellow]
    """
    trader.contracts()


@trader_command()
def ships():
    """
    Print out information for all ships the active agent has access to. Ex: [yellow]cli.py ships[/yellow]
    """
    trader.ships()


@trader_command()
@click.argument("call_sign")
def ship(call_sign: str):
    """
    Print out information for a specific ship by a provided call sign. Ex: [yellow]cli.py ship CALL_SIGN[/yellow]
    """
    trader.ship(call_sign=call_sign)


@trader_command()
def systems():
    """
    Print out information for all systems. Ex: [yellow]cli.py systems[/yellow]
    """
    trader.systems()


@trader_command()
@click.argument("symbol")
def system(symbol: str):
    """
    Print out information for a specific system by a provided symbol. Ex: [yellow]cli.py system SYMBOL[/yellow]
    """
    trader.system(symbol=symbol)


@trader_command()
@click.argument("system_symbol")
def waypoints(system_symbol: str):
    """
    Print out information for all waypoints for a provided system symbol. Ex: [yellow]cli.py waypoints SYMBOL[/yellow]
    """
    trader.waypoints(system_symbol=system_symbol)


@trader_command()
@click.argument("system_symbol")
@click.argument("waypoint_symbol")
def waypoint(system_symbol: str, waypoint_symbol: str):
    """
    Print out information for all waypoints for a provided system symbol. Ex: [yellow]cli.py waypoints SYMBOL[/yellow]
    """
    trader.waypoint(system_symbol=system_symbol, waypoint_symbol=waypoint_symbol)


@trader_command()
@click.argument("call_sign")
def dock(call_sign: str):
    """
    Attempts to dock a ship based on a provided call sign. Ex: [yellow]cli.py dock CALL_SIGN[/yellow]
    """
    trader.dock(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
def refuel(call_sign: str):
    """
    Attempts to refuel a ship based on a provided call sign. Ex: [yellow]cli.py refuel CALL_SIGN[/yellow]
    """
    trader.refuel(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
def orbit(call_sign: str):
    """
    Attempts to orbit a ship based on a provided call sign. Ex: [yellow]cli.py orbit CALL_SIGN[/yellow]
    """
    trader.orbit(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
def cooldown(call_sign: str):
    """
    Prints active cooldown information for a given ship by its call sign. Ex: [yellow]cli.py cooldown CALL_SIGN[/yellow]
    """
    trader.cooldown(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
def extract(call_sign: str):
    """
    Attempts to start extraction from a ship based on a provided call sign. Ex: [yellow]cli.py extract CALL_SIGN[/yellow]
    """
    trader.extract(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
@click.argument("waypoint_symbol")
def navigate(call_sign: str, waypoint_symbol: str):
    """
    Attempts to navigate a ship based on a provided call sign towards a provided waypoint symbol. Ex: [yellow]cli.py navigate CALL_SIGN WAYPOINT_SYMBOL[/yellow]
    """
    trader.navigate(call_sign=call_sign, waypoint_symbol=waypoint_symbol)


@trader_command()
@click.argument("system_symbol")
@click.argument("waypoint_symbol")
def market(system_symbol: str, waypoint_symbol: str):
    """
    Prints market information for a provided system and waypoint symbol. Ex: [yellow]cli.py market SYSTEM_SYMBOL WAYPOINT_SYMBOL[/yellow]
    """
    trader.market(system_symbol=system_symbol, waypoint_symbol=waypoint_symbol)


@trader_command()
@click.argument("system_symbol")
@click.argument("waypoint_symbol")
def shipyard(system_symbol: str, waypoint_symbol: str):
    """
    Prints shipyard information for a provided system and waypoint symbol. Ex: [yellow]cli.py shipyard SYSTEM_SYMBOL WAYPOINT_SYMBOL[/yellow]
    """
    trader.shipyard(system_symbol=system_symbol, waypoint_symbol=waypoint_symbol)


@trader_command()
@click.argument("call_sign")
def cargo(call_sign: str):
    """
    Prints cargo for a given ship based on a provided call sign. Ex: [yellow]cli.py cargo CALL_SIGN[/yellow]
    """
    trader.cargo(call_sign=call_sign)


@trader_command()
@click.argument("call_sign")
@click.argument("flight_mode")
def set_flight_mode(call_sign: str, flight_mode: FlightModes):
    """
    Sets flight mode for a given ship based on a provided call sign. Ex: [yellow]cli.py set-flight-mode CALL_SIGN FLIGHT_MODE[/yellow]
    """
    trader.set_flight_mode(call_sign=call_sign, flight_mode=flight_mode)


@trader_command()
@click.argument("call_sign")
@click.argument("symbol")
@click.argument("units")
def sell(call_sign: str, symbol: str, units: int):
    """
    Attempts to conduct a sale for a given ship's call sign, and will sell X units (provided) of Y symbols (provided). Ex: [yellow]cli.py sell CALL_SIGN SYMBOL UNITS[/yellow]
    """
    trader.sell(call_sign=call_sign, symbol=symbol, units=units)


@trader_command()
@click.argument("waypoint_symbol")
@click.argument("ship_type")
def purchase_ship(waypoint_symbol: str, ship_type: str):
    """
    Starts purchase of a ship with a payload. Requires another ship at its station.  Ex: [yellow]cli.py purchase-ship WAYPOINT_SYMBOL SHIP_TYPE [/yellow]
    """
    trader.purchase_ship(waypoint_symbol=waypoint_symbol, ship_type=ship_type)


@trader_command()
@click.argument("call_sign")
@click.option(
    "--repeat",
    default=False,
    help="Apply this flag if you want to run this logic loop repeatedly",
)
def miner_trader_loop(call_sign: str, repeat: bool):
    """
    Begins a naive mine, refuel, and sell loop for a given call sign. Ex: [yellow]cli.py miner-trader-loop --repeat true CALL_SIGN[/yellow]
    """
    trader.miner_trader_loop(call_sign=call_sign, repeat=repeat)


@trader_command()
@click.argument("call_sign")
@click.option(
    "--repeat",
    default=False,
    help="Apply this flag if you want to run this logic loop repeatedly",
)
def explorer_loop(call_sign: str, repeat: bool):
    """
    Begins a naive exploration loop for a given call sign. Ex: [yellow]cli.py explorer-loop --repeat true CALL_SIGN[/yellow]
    """
    trader.explorer_loop(call_sign=call_sign, repeat=repeat)


@trader_command()
def fleet_loop():
    """
    Begins a naive set of loops for all ships in the fleet. Ex: [yellow]cli.py fleet-loop [/yellow]
    """
    trader.fleet_loop()


@trader_command()
def fleet_summary():
    """
    Print out a summary table of the fleet and its ongoing actions. Ex: [yellow]cli.py fleet-summary[/yellow]
    """
    trader.fleet_summary()


@trader_command()
@click.argument("call_sign")
def ship_summary(call_sign: str):
    """
    Print out a summary table of a ship and its recent history. Ex: [yellow]cli.py ship-summary CALL_SIGN[/yellow]
    """
    trader.fleet_summary(call_sign=call_sign, limit=20)


@trader_command()
def agent_history():
    """
    Print out a summary table of an agent and its recent history. Ex: [yellow]cli.py agent-history[/yellow]
    """
    trader.agent_history()


# unique status cli command of backend
cli.add_command(status)

# basic cli commands
cli.add_command(agent)
cli.add_command(agents)
cli.add_command(cargo)
cli.add_command(contracts)
cli.add_command(cooldown)
cli.add_command(dock)
cli.add_command(extract)
cli.add_command(refuel)
cli.add_command(market)
cli.add_command(navigate)
cli.add_command(orbit)
cli.add_command(purchase_ship)
cli.add_command(register)
cli.add_command(sell)
cli.add_command(set_flight_mode)
cli.add_command(ships)
cli.add_command(ship)
cli.add_command(shipyard)
cli.add_command(system)
cli.add_command(systems)
cli.add_command(waypoint)
cli.add_command(waypoints)

# commands for testing more complex behaviors
cli.add_command(explorer_loop)
cli.add_command(miner_trader_loop)
cli.add_command(fleet_loop)

# commands for actions taken against the entire fleet or summary actions
cli.add_command(fleet_summary)
cli.add_command(ship_summary)
cli.add_command(agent_history)

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.SHOW_METAVARS_COLUMN = False
click.rich_click.APPEND_METAVARS_HELP = True
click.rich_click.COMMAND_GROUPS = {
    "cli.py": [
        {
            "name": "Logical Loops and Fleet Commands",
            "commands": ["explorer-loop", "miner-trader-loop", "fleet-loop"],
        },
        {
            "name": "Summaries and Reports",
            "commands": ["fleet-summary", "ship-summary", "agent-history"],
        },
    ]
}

if __name__ == "__main__":
    cli.main(standalone_mode=True)
