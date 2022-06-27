import os
from typing import Iterable
from typing import Literal
from typing import Type

import plotly.express as xp
import plotly.graph_objects as go
from echostats._abc import BaseConsumer
from echostats._abc import BaseGrapher
from echostats._abc import ConsumerDependent
from echostats._abc import ConsumerMapping
from echostats.models import ConsumerEvent
from echostats.models import Disc
from echostats.models import EchoEvent
from echostats.models import GameStatus
from echostats.models import Vector3D
from PIL import Image


class GoalsConsumer(BaseConsumer):
    def __init__(
        self, perspective_of_striker: bool = True, perspective_of_goalie: bool = False
    ):
        if perspective_of_striker + perspective_of_goalie > 1:
            raise ValueError(
                "perspective_of_striker and perspective_of_goalie are mutually exclusive"
            )
        elif perspective_of_striker + perspective_of_goalie == 0:
            raise ValueError(
                "specify one of the following parameters: perspective_of_striker and "
                "perspective_of_goalie are mutually exclusive"
            )
        self.orange_x_factor = 1
        self.blue_x_factor = 1
        if perspective_of_striker:
            self.orange_x_factor = -1
            self.blue_x_factor = 1
        elif perspective_of_goalie:
            self.orange_x_factor = 1
            self.blue_x_factor = -1
        self._orange_goals: list[Vector3D] = list()
        self._blue_goals: list[Vector3D] = list()

    def consume(self, event: ConsumerEvent) -> None:
        match event.echo_event:
            case EchoEvent(
                game_status=None,
                last_score=_,
            ):
                disc = event.echo_event.disc
                if disc is None:
                    pass
                elif round(disc.position.z) == 36:
                    pos = disc.position.copy()
                    pos.x *= self.orange_x_factor
                    self._orange_goals.append(pos)
                elif round(disc.position.z) == -36:
                    pos = disc.position.copy()
                    pos.y *= self.blue_x_factor
                    self._blue_goals.append(pos)

    @property
    def orange_goals(self) -> list[Vector3D]:
        return self._orange_goals

    @property
    def blue_goals(self) -> list[Vector3D]:
        return self._blue_goals


class GoalsGrapher(BaseGrapher, ConsumerDependent):
    def __init__(self, team: Literal["blue", "orange"]):
        self.team = team

    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (GoalsConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.goals_consumer = dependencies[GoalsConsumer]

    def generate_figure(self) -> go.Figure:
        if self.team == "blue":
            goals = self.goals_consumer.blue_goals
            color = "blue"
        else:
            goals = self.goals_consumer.orange_goals
            color = "orange"

        if len(goals) > 0:
            fig = xp.scatter(x=[i.x for i in goals], y=[i.y for i in goals])
        else:
            fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[-1.5, 0, 1.5, 0, -1.5],
                y=[0, 1.5, 0, -1.5, 0],
                fill="toself",
                marker=dict(color=color),
            )
        )
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        fig.update_layout(
            showlegend=False,
        )
        return fig


class DiscPlayingConsumer(BaseConsumer):
    def __init__(self):
        self._disc_positions: list[Disc] = []

    def consume(self, event: ConsumerEvent) -> None:
        match event.echo_event:
            case EchoEvent(
                game_status=GameStatus.PLAYING,
            ):
                self._disc_positions.append(event.echo_event.disc)

    @property
    def disc_positions(self) -> list[Disc]:
        return [i.copy() for i in self._disc_positions]


app_path = os.path.dirname(os.path.abspath(__file__))


class DiscPlayingGrapher(BaseGrapher, ConsumerDependent):
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (DiscPlayingConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.disc_playing_consumer = dependencies[DiscPlayingConsumer]

    def generate_figure(self) -> go.Figure:
        discs = self.disc_playing_consumer.disc_positions
        fig = go.Figure()
        fig.add_scatter(
            x=[i.position.z for i in discs],
            y=[i.position.x for i in discs],
            mode="lines+markers",
        )
        fig.update_yaxes(
            scaleanchor="x",
            scaleratio=1,
        )
        y = 16
        fig.add_layout_image(
            dict(
                source=Image.open(
                    os.path.join(
                        app_path, "../assets/sean-ian-runnels-echo-arena-003.png"
                    )
                ),
                xref="x",
                yref="y",
                x=-40,
                y=y,
                sizex=80,
                sizey=y * 2,
                sizing="stretch",
                opacity=0.5,
                layer="below",
            )
        )

        # Set templates
        fig.update_layout(template="plotly_white")
        return fig
