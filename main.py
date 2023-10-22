import click

from trader.main import RegistrationFields, Trader


@click.group()
def cli():
    pass


@click.command()
@click.argument("call_sign")
@click.argument("faction", type=click.Choice(['COSMIC']))
def register(call_sign: str, faction: str):
    """Registers and stores token locally"""
    click.echo(f"Registering client for call_sign: {call_sign} ({faction})")
    trader = Trader()
    details = RegistrationFields(call_sign=call_sign, faction=faction)
    trader.register(data=details)

@click.command()
def agent():
    trader = Trader()
    trader.agent()

cli.add_command(register)
cli.add_command(agent)


if __name__ == "__main__":
    cli()
