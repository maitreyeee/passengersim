import time
from pathlib import Path

import typer

import passengersim as pax
from passengersim.cli._app import app

from .info import info


@app.command()
def run(
    config_files: list[Path] = typer.Option(  # noqa: B008
        ...,
        "-c",
        "--config",
        help="Configuration file(s) that defines the network and various simulation options.",
    ),
):
    info()
    start_time = time.time()
    sim = pax.Simualtion.from_yaml(config_files)
    sim.run(log_reports=False)
    print(time.time() - start_time)
