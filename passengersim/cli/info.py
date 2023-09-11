from passengersim_core import build_expiration
from passengersim_core._version import __version__ as __core_version__
from passengersim_core.cli._app import app
from rich import print

from passengersim._version import __version__


@app.command()
def info():
    print(
        f"""\
:seat: [bold dark_goldenrod]PassengerSim[/bold dark_goldenrod]
  [black not bold]Version {__version__}
  Core Version {__core_version__}
  Copyright (c) 2023
  This in-development tool is not for public distribution.
  [red]This build expires {build_expiration().astimezone()}[/red]
  [link=https://www.passengersim.com/]https://www.passengersim.com[/link]
"""
    )
