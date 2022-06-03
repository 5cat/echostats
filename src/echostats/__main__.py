import click
from echostats import FileStreamer
from echostats import OnlineStreamer
from echostats.consumers import DebuggerConsumer
from echostats.consumers import RecorderConsumer


@click.group()
def cli():
    ...


@cli.command()
@click.option("--ip", required=True)
@click.option("--rate", default=10)
def online(ip: str, rate: float):
    streamer = OnlineStreamer(ip=ip, rate=rate)
    streamer.consume(consumers=[DebuggerConsumer()])


@cli.command()
@click.option("--path", required=True)
def file(path: str):
    streamer = FileStreamer(path=path)
    streamer.consume(consumers=[DebuggerConsumer()])


@cli.command()
@click.option("--ip", required=True)
@click.option("--rate", default=10)
@click.option("--path", required=True)
def record(ip: str, rate: float, path: str):
    streamer = OnlineStreamer(ip=ip, rate=rate)
    streamer.consume(consumers=[RecorderConsumer(path=path)])


cli()
