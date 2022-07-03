import math
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
from echostats.models import EchoEvent
from echostats.models import GameStatus
from echostats.models import Stats
from echostats.models import Vector3D
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

        df = pd.DataFrame(data)
        df.sort_values("time")
        fig = xp.line(df, x="time", y="ping", color="name", title="Players' Ping")
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
            "Goals": "goals",
            "Points": "points",
            "Assists": "assists",
            "Passes": "passes",
            "Saves": "saves",
            "Stuns": "stuns",
            "Blocks": "blocks",
            "Steals": "steals",
            "Shots": "shots_taken",
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

        fig = make_subplots(rows=rows, cols=cols, specs=spec)

        for i, stat_name in enumerate(stats_attributes):
            dfa = df.query(f'stat_name == "{stat_name}"')
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

        fig.update_layout(
            showlegend=False, height=rows * 250, title_text="Player Stats"
        )
        return fig


class PlayerPositionConsumer(BaseConsumer):
    def __init__(self):
        self._data: dict[str, dict[str, dict[datetime, Vector3D]]] = {}

    def consume(self, event: ConsumerEvent) -> None:
        match event.echo_event:
            case EchoEvent(
                game_status=GameStatus.PLAYING,
            ):
                for team in event.echo_event.teams:
                    if team.name not in self._data:
                        self._data[team.name] = {}
                    if team.players is None:
                        continue
                    for player in team.players:
                        if player.name not in self._data[team.name]:
                            self._data[team.name][player.name] = {}

                        self._data[team.name][player.name][
                            event.stream_event.datetime
                        ] = player.head.position

    @property
    def data(self):
        return self._data


class PlayerDistanceNetworkGrapher(BaseGrapher, ConsumerDependent):
    # TODO: this class might need refactoring, or might leave it at his
    player_position_consumer: PlayerPositionConsumer

    def __init__(self):
        self.min_distance: float | None = None
        self.max_distance: float | None = None

    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (PlayerPositionConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.player_position_consumer = dependencies[PlayerPositionConsumer]

    def calculate_distance_3d(self, a: Vector3D, b: Vector3D) -> float:
        return pow(
            sum(
                (
                    pow(a.x - b.x, 2),
                    pow(a.y - b.y, 2),
                    pow(a.z - b.z, 2),
                )
            ),
            0.5,
        )

    def calculate_distance_2d(
        self, a: tuple[float, float], b: tuple[float, float]
    ) -> float:
        return pow(
            sum(
                (
                    pow(a[0] - b[0], 2),
                    pow(a[1] - b[1], 2),
                )
            ),
            0.5,
        )

    def calculate_mid_point_2d(
        self, a: tuple[float, float], b: tuple[float, float], shift: float = 0
    ) -> tuple[float, float]:
        a_x, a_y = tuple([i * (1 - shift) for i in a])
        b_x, b_y = tuple([i * (1 + shift) for i in b])
        return (a_x + b_x) / 2, (a_y + b_y) / 2

    def generate_node_positions(self, a: list[str]) -> dict[str, tuple[float, float]]:
        # https://nerdparadise.com/programming/pygameregularpolygon
        data = {}
        x = 0.0
        y = 0.0
        radius = 1
        tiltAngle = 0
        numSides = len(a)
        for i, item in enumerate(a):
            x = x + radius * math.cos(tiltAngle + math.pi * 2 * i / numSides)
            y = y + radius * math.sin(tiltAngle + math.pi * 2 * i / numSides)
            data[item] = (x, y)
        return data

    def normalize_distance(self, d: float) -> float:
        return 1 - ((d - self.min_distance) / (self.max_distance - self.min_distance))

    def generate_figure(self) -> go.Figure:

        adjacency_matrix: dict[str, dict[str, dict[str, float]]] = {}
        for team_name, player_data in self.player_position_consumer.data.items():
            if team_name == "SPECTATORS":
                continue
            player_names = player_data.keys()
            for player_1 in player_names:
                for player_2 in player_names:
                    if player_2 == player_1:
                        continue
                    player_1_times = set(player_data[player_1].keys())
                    player_2_times = set(player_data[player_2].keys())
                    player_shared_times = player_1_times.intersection(player_2_times)
                    if len(player_shared_times) == 0:
                        continue
                    all_distances = [
                        self.calculate_distance_3d(
                            player_data[player_1][t], player_data[player_2][t]
                        )
                        for t in player_shared_times
                    ]
                    average_distance = sum(all_distances) / len(all_distances)
                    if team_name not in adjacency_matrix:
                        adjacency_matrix[team_name] = {}
                    if player_1 not in adjacency_matrix[team_name]:
                        adjacency_matrix[team_name][player_1] = {}
                    if player_2 not in adjacency_matrix[team_name]:
                        adjacency_matrix[team_name][player_2] = {}
                    adjacency_matrix[team_name][player_1][player_2] = average_distance
                    adjacency_matrix[team_name][player_2][player_1] = average_distance
                    if (
                        self.min_distance is None
                        or average_distance < self.min_distance
                    ):
                        self.min_distance = average_distance
                    if (
                        self.max_distance is None
                        or average_distance > self.max_distance
                    ):
                        self.max_distance = average_distance

        fig = make_subplots(rows=1, cols=2, subplot_titles=("Orange Team", "Blue Team"))

        for col, team_name in enumerate(["ORANGE TEAM", "BLUE TEAM"]):
            col += 1
            fig.update_xaxes(
                visible=False,
                row=1,
                col=col,
            )
            fig.update_yaxes(
                visible=False,
                row=1,
                col=col,
            )

            if team_name not in adjacency_matrix:
                continue
            all_orange_players: set[str] = set()
            all_orange_players.update(adjacency_matrix[team_name].keys())
            for other_keys in adjacency_matrix[team_name].values():
                all_orange_players.update(other_keys.keys())
            orange_2d_edges = self.generate_node_positions(list(all_orange_players))

            plotted_lines = set()
            for player_1, rest in adjacency_matrix[team_name].items():
                for player_2, weight in rest.items():
                    player_line = frozenset({player_1, player_2})
                    if player_line in plotted_lines:
                        continue
                    plotted_lines.add(player_line)
                    fig.add_trace(
                        go.Scatter(
                            x=[
                                orange_2d_edges[player_1][0],
                                orange_2d_edges[player_2][0],
                            ],
                            y=[
                                orange_2d_edges[player_1][1],
                                orange_2d_edges[player_2][1],
                            ],
                            mode="lines",
                            hoverinfo="skip",
                            line=dict(width=18 * self.normalize_distance(weight) + 2),
                        ),
                        row=1,
                        col=col,
                    )
                    if (
                        self.calculate_distance_2d(
                            orange_2d_edges[player_1], orange_2d_edges[player_2]
                        )
                        - 1
                        <= 1e-6
                    ):
                        shift = 0.0
                    else:
                        shift = 0.5
                    x_mid, y_mid = self.calculate_mid_point_2d(
                        orange_2d_edges[player_1],
                        orange_2d_edges[player_2],
                        shift=shift,
                    )
                    fig.add_annotation(
                        x=x_mid,
                        y=y_mid,
                        text=str(round(weight, 3)),
                        row=1,
                        col=col,
                    )
            fig.add_trace(
                go.Scatter(
                    x=[i[0] for i in orange_2d_edges.values()],
                    y=[i[1] for i in orange_2d_edges.values()],
                    mode="markers+text",
                    marker=dict(size=30),
                    text=list(orange_2d_edges.keys()),
                    hoverinfo="skip",
                    textposition="top center",
                ),
                row=1,
                col=col,
            )

        fig.update_layout(
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            xaxis_zeroline=False,
            yaxis_zeroline=False,
            showlegend=False,
            title_text="Average Distance Graph",
        )

        return fig
