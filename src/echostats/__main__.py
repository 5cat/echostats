import click
from echostats.streamer import FileStreamer
from echostats.streamer import OnlineStreamer


@click.group()
def cli():
    ...


@cli.command()
@click.option("--ip", required=True)
@click.option("--rate", default=10, required=True)
def online(ip: str, rate: float):
    streamer = OnlineStreamer(ip=ip, rate=rate)
    for i in streamer.consume():
        print(repr(i.last_score))


@cli.command()
@click.option("--path", required=True)
def file(path: str):
    streamer = FileStreamer(path=path)
    for i in streamer.consume():
        ...
        # print(repr(i.teams[0].players))


cli()
