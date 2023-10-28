import os

import click
from loguru import logger

from trader.exceptions import TraderException
from trader.main import Trader
from trader.client.registration import RegistrationRequestData
from trader.print import print_alert


if "DEBUG" not in os.environ:
    logger.remove()
    logger.add("out.log")

def close_cli(code: int = 0):
    os._exit(code)


class ClickCommandWrapper(click.Command):
    def invoke(self, ctx):
        try:
            super().invoke(ctx)
        except TraderException as e:
            print_alert(message=f"Error encountered: {e.message}", console=trader.console)
            close_cli(code=1)
        except Exception as e:
            close_cli(code=1)


def trader_command(func=None, **kwargs):
    def decorator(func):
        return click.command(cls=ClickCommandWrapper, **kwargs)(func)
    return decorator if func is None else decorator(func)


trader = Trader()
@click.group()
@click.pass_context
def cli(ctx):
    ctx.call_on_close(close_cli)


@trader_command()
@click.argument("call_sign")
@click.argument("faction", type=click.Choice(['COSMIC']))
def register(call_sign: str, faction: str):
    """Registers and stores token locally"""
    click.echo(f"Registering client for call_sign: {call_sign} ({faction})")
    details = RegistrationRequestData(call_sign=call_sign, faction=faction)
    trader.register(data=details)

@trader_command()
def agent():
    trader.agent()

@trader_command()
def agents():
    trader.agents()

@trader_command()
def contracts():
    trader.contracts()

@trader_command()
def ships():
    trader.ships()

@trader_command()
@click.argument("call_sign")
def ship(call_sign: str):
    trader.ship(call_sign=call_sign)

@trader_command()
def systems():
    trader.systems()

@trader_command()
@click.argument("symbol")
def system(symbol: str):
    trader.system(symbol=symbol)

@trader_command()
@click.argument("system_symbol")
def waypoints(system_symbol: str):
    trader.waypoints(system_symbol=system_symbol)

@trader_command()
@click.argument("call_sign")
def dock(call_sign: str):
    trader.dock(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
def refuel(call_sign: str):
    trader.refuel(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
def orbit(call_sign: str):
    trader.orbit(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
def cooldown(call_sign: str):
    trader.cooldown(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
def extract(call_sign: str):
    trader.extract(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
@click.argument("waypoint_symbol")
def navigate(call_sign: str, waypoint_symbol: str):
    trader.navigate(call_sign=call_sign, waypoint_symbol=waypoint_symbol)

@trader_command()
@click.argument("system_symbol")
@click.argument("waypoint_symbol")
def market(system_symbol: str, waypoint_symbol: str):
    trader.market(system_symbol=system_symbol, waypoint_symbol=waypoint_symbol)

@trader_command()
@click.argument("call_sign")
def cargo(call_sign: str):
    trader.cargo(call_sign=call_sign)

@trader_command()
@click.argument("call_sign")
@click.argument("symbol")
@click.argument("units")
def sell(call_sign: str, symbol: str, units: int):
    trader.sell(call_sign=call_sign, symbol=symbol, units=units)

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
cli.add_command(register)
cli.add_command(sell)
cli.add_command(ships)
cli.add_command(ship)
cli.add_command(system)
cli.add_command(systems)
cli.add_command(waypoints)


if __name__ == "__main__":
    cli()
