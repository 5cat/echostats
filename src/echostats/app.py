# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pandas as pd
import plotly.express as px
from dash import Dash
from dash import dcc
from dash import html
from echostats import FileStreamer
from echostats.consumers.disc import DiscPlayingConsumer
from echostats.consumers.disc import DiscPlayingGrapher
from echostats.consumers.disc import GoalsConsumer
from echostats.consumers.disc import GoalsGrapher
from echostats.consumers.player import PingConsumer
from echostats.consumers.player import PingGrapher
from echostats.consumers.player import PlayerStatsGrapher

app = Dash(__name__)

colors = {"background": "#111111", "text": "#7FDBFF"}


streamer = FileStreamer("/media/SSD/echostats/test.echoarena")

goals_grapher_blue = GoalsGrapher(team="blue")
goals_grapher_orange = GoalsGrapher(team="orange")
ping_grapher = PingGrapher()
disc_playing_grapher = DiscPlayingGrapher()
player_stats_grapher = PlayerStatsGrapher()
streamer.resolve(
    [
        goals_grapher_blue,
        goals_grapher_orange,
        ping_grapher,
        disc_playing_grapher,
        player_stats_grapher,
    ]
)


def fig_post_process(fig):
    fig.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"],
    )
    return fig


app.layout = html.Div(
    style={"backgroundColor": colors["background"]},
    children=[
        html.H1(
            children="Hello Dash",
            style={"textAlign": "center", "color": colors["text"]},
        ),
        html.Div(
            children="Dash: A web application framework for your data.",
            style={"textAlign": "center", "color": colors["text"]},
        ),
        dcc.Graph(
            id="example-graph-2",
            figure=fig_post_process(goals_grapher_blue.generate_figure()),
        ),
        dcc.Graph(
            id="example-graph-3",
            figure=fig_post_process(goals_grapher_orange.generate_figure()),
        ),
        dcc.Graph(
            id="example-graph-4",
            figure=fig_post_process(disc_playing_grapher.generate_figure()),
        ),
        dcc.Graph(
            id="example-graph-5",
            figure=fig_post_process(ping_grapher.generate_figure()),
        ),
        dcc.Graph(
            id="example-graph-6",
            figure=fig_post_process(player_stats_grapher.generate_figure()),
        ),
    ],
)


if __name__ == "__main__":
    app.run_server(debug=True)
