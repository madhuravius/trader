from typing import Any, List

from rich import inspect
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def print_alert(message: str, console: Console) -> None:
    console.print(Panel(message))


def print_as_table(title: str, data: List[Any], console: Console) -> None:
    if not data:
        return console.print(Panel(f"No data to print for {title}"))

    table = Table(title=title)
    keys = []

    for column in data[0].to_dict().keys():
        keys.append(column)
        table.add_column(column)

    nested_data_found = False
    for datum in data:
        if nested_data_found:
            break
        dict_datum = datum.to_dict()
        values_in_row = []
        for key in keys:
            if isinstance(dict_datum[key], dict):
                nested_data_found = True
                break
            values_in_row.append(str(dict_datum[key]))
        table.add_row(*values_in_row)

    if nested_data_found:
        [inspect(datum, value=False) for datum in data]
    else:
        console.print(table)
