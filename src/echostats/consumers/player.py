from datetime import datetime
from math import ceil
from typing import Iterable
from typing import Type

import pandas as pd
import plotly.express as xp
import plotly.graph_objects as go
from echostats._abc import BaseConsumer
from echostats._abc import BaseGrapher
from echostats._abc import ConsumerDependent
from echostats._abc import ConsumerMapping
from echostats.models import ConsumerEvent
from echostats.models import Stats
from echostats.models import TeamEnum
from plotly.subplots import make_subplots


class PingConsumer(BaseConsumer):
    def __init__(self):
        self._teams: dict[str, dict[str, dict[datetime, int]]] = {}

    def consume(self, event: ConsumerEvent) -> None:
        for team in event.echo_event.teams:
            players = team.players if team.players is not None else []
            if team.name not in self._teams:
                self._teams[team.name] = {}
            for player in players:
                if player.name not in self._teams[team.name]:
                    self._teams[team.name][player.name] = {}
                self._teams[team.name][player.name][
                    event.stream_event.datetime
                ] = player.ping

    @property
    def pings(self) -> dict[str, dict[str, dict[datetime, int]]]:
        return self._teams


class PingGrapher(BaseGrapher, ConsumerDependent):
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (PingConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.ping_consumer = dependencies[PingConsumer]

    def generate_figure(self) -> go.Figure:
        data = []
        for team_name, players in self.ping_consumer.pings.items():
            for player_name, player_pings in players.items():
                for dtime, ping in player_pings.items():
                    data.append({"time": dtime, "ping": ping, "name": player_name})

        fig = xp.line(pd.DataFrame(data), x="time", y="ping", color="name")
        return fig


class PlayerStatsConsumer(BaseConsumer):
    def __init__(self):
        self._teams: dict[str, dict[str, Stats]] = {}

    def consume(self, event: ConsumerEvent) -> None:
        for team in event.echo_event.teams:
            players = team.players if team.players is not None else []
            if team.name not in self._teams:
                self._teams[team.name] = {}
            for player in players:
                self._teams[team.name][player.name] = player.stats

    @property
    def players_stats(self) -> dict[str, dict[str, Stats]]:
        return self._teams


class PlayerStatsGrapher(BaseGrapher, ConsumerDependent):
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (PlayerStatsConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.player_stats_consumer = dependencies[PlayerStatsConsumer]

    def generate_figure(self) -> go.Figure:
        data = []
        stats_attributes = {
            "goals": "goals",
            "points": "points",
            "stuns": "stuns",
            "saves": "saves",
        }
        cols = 3
        rows = ceil(len(stats_attributes) / cols)

        for team_name, players in self.player_stats_consumer.players_stats.items():
            for player_name, player_stats in players.items():
                for stat_name, stat_attribute_name in stats_attributes.items():
                    stat_value = getattr(player_stats, stat_attribute_name)
                    if stat_value == 0:
                        continue
                    data.append(
                        {
                            "player_name": player_name,
                            "team_name": team_name,
                            "stat_name": stat_name,
                            "stat_value": stat_value,
                            "team_color": "orange"
                            if "orange" in team_name.lower()
                            else "blue",
                        }
                    )

        df = pd.DataFrame(data)
        i = 0
        spec = []
        for row_i in range(rows):
            row_spec = []
            for col_i in range(cols):
                if i < len(stats_attributes):
                    row_spec.append({"type": "pie"})
                else:
                    row_spec.append(None)
                i += 1
            spec.append(row_spec)
            if i > len(stats_attributes):
                break

        print(spec)
        fig = make_subplots(rows=rows, cols=cols, specs=spec)

        for i, stat_name in enumerate(stats_attributes):
            dfa = df.query(f'stat_name == "{stat_name}"')
            print(f"{i//cols + 1=}, {(i % cols) + 1=}")
            fig.add_trace(
                go.Pie(
                    values=dfa["stat_value"],
                    labels=dfa["player_name"],
                    textinfo="label+value",
                    marker=dict(colors=dfa["team_color"]),
                    title=dict(text=stat_name),
                    sort=False,
                ),
                row=i // cols + 1,
                col=(i % cols) + 1,
            )

        return fig
