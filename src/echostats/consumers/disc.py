import os
from typing import Iterable
from typing import Optional
from typing import Type
from typing import TypedDict

import pandas as pd
import plotly.graph_objects as go
from echostats._abc import BaseConsumer
from echostats._abc import BaseGrapher
from echostats._abc import ConsumerDependent
from echostats._abc import ConsumerMapping
from echostats.models import ConsumerEvent
from echostats.models import Disc
from echostats.models import EchoEvent
from echostats.models import GameStatus
from echostats.models import Player
from echostats.models import Vector3D
from PIL import Image
from plotly.subplots import make_subplots


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
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (GoalsConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.goals_consumer = dependencies[GoalsConsumer]

    def create_per_team_plot(
        self, goals: list[Vector3D], color: str, fig: go.Figure, row: int, col: int
    ) -> go.Figure:
        if len(goals) > 0:
            fig.add_scatter(
                x=[i.x for i in goals],
                y=[i.y for i in goals],
                marker=dict(color="white", symbol="x", size=15),
                mode="markers",
                row=row,
                col=col,
            )
        fig.add_trace(
            go.Scatter(
                x=[-1.5, 0, 1.5, 0, -1.5],
                y=[0, 1.5, 0, -1.5, 0],
                fill="toself",
                marker=dict(color=color),
                hovertext="skip",
            ),
            row=row,
            col=col,
        )
        fig.update_yaxes(
            visible=False,
            scaleanchor="x",
            scaleratio=1,
            row=row,
            col=col,
        )
        fig.update_xaxes(
            visible=False,
            scaleanchor="y",
            scaleratio=1,
            row=row,
            col=col,
        )
        return fig

    def generate_figure(self) -> go.Figure:
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Goals on Orange", "Goals on Blue"),
            specs=[[{"type": "scatter"}, {"type": "scatter"}]],
        )
        self.create_per_team_plot(
            self.goals_consumer.blue_goals,
            color="orange",
            fig=fig,
            row=1,
            col=1,
        )

        self.create_per_team_plot(
            self.goals_consumer.orange_goals,
            color="blue",
            fig=fig,
            row=1,
            col=2,
        )

        fig.update_layout(
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            xaxis_zeroline=False,
            yaxis_zeroline=False,
            showlegend=False,
            title_text="Goal Positions",
        )
        return fig


class DiscPlayingStruct(TypedDict):
    disc: Disc
    player_name: Optional[str]
    team_name: Optional[str]


class DiscPlayingConsumer(BaseConsumer):
    def __init__(self):
        self._disc_positions = []

    def consume(self, event: ConsumerEvent) -> None:
        match event.echo_event:
            case EchoEvent(
                game_status=GameStatus.PLAYING,
            ):
                if event.echo_event.disc is not None:
                    poss = event.echo_event.possession
                    if (
                        poss is not None
                        and poss.team is not None
                        and poss.player is not None
                    ):
                        team = event.echo_event.teams[poss.team]
                        player_name = team.players[poss.player].name
                        team_name = {"BLUE TEAM": "blue", "ORANGE TEAM": "orange"}[
                            team.name
                        ]
                    else:
                        player_name = None
                        team_name = None

                    self._disc_positions.append(
                        DiscPlayingStruct(
                            disc=event.echo_event.disc,
                            player_name=player_name,
                            team_name=team_name,
                        )
                    )

    @property
    def disc_positions(self) -> list[DiscPlayingStruct]:
        return [i.copy() for i in self._disc_positions]


app_path = os.path.dirname(os.path.abspath(__file__))


class DiscPlayingGrapher(BaseGrapher, ConsumerDependent):
    def get_dependencies(self) -> Iterable[Type[BaseConsumer]]:
        return (DiscPlayingConsumer,)

    def init(self, dependencies: ConsumerMapping) -> None:
        self.disc_playing_consumer = dependencies[DiscPlayingConsumer]

    def generate_figure(self) -> go.Figure:
        discs_struct = self.disc_playing_consumer.disc_positions
        fig = go.Figure()

        fig.add_scatter(
            x=[i["disc"].position.z for i in discs_struct],
            y=[i["disc"].position.x for i in discs_struct],
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

        fig.update_yaxes(
            visible=False,
            range=(-16, 16),
        )
        fig.update_xaxes(
            visible=False,
            range=(-40, 40),
        )

        # Set templates
        fig.update_layout(
            xaxis_showgrid=False,
            yaxis_showgrid=False,
            xaxis_zeroline=False,
            yaxis_zeroline=False,
            template="plotly_white",
        )
        return fig
