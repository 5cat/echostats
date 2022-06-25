import os

import plotly.express as xp
import plotly.graph_objects as go
from echostats.models import Disc
from echostats.models import Vector3D
from PIL import Image

app_path = os.path.dirname(os.path.abspath(__file__))


def create_goal_plot(goals: list[Vector3D], color="pink"):
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


def create_disc_plot(discs: list[Disc]):
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
                os.path.join(app_path, "../assets/sean-ian-runnels-echo-arena-003.png")
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
