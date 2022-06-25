# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pandas as pd
import plotly.express as px
from dash import Dash
from dash import dcc
from dash import html
from echostats import FileStreamer
from echostats.consumers.disc import DiscPlayingConsumer
from echostats.consumers.disc import GoalsConsumer
from echostats.graphers.disc import create_disc_plot
from echostats.graphers.disc import create_goal_plot

app = Dash(__name__)

colors = {"background": "#111111", "text": "#7FDBFF"}


streamer = FileStreamer("/media/SSD/echostats/test3.echoarena")
goals_consumer = GoalsConsumer()
disc_playing_consumer = DiscPlayingConsumer()

streamer.consume([goals_consumer, disc_playing_consumer])


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
            figure=fig_post_process(
                create_goal_plot(goals_consumer.blue_goals, color="blue")
            ),
        ),
        dcc.Graph(
            id="example-graph-3",
            figure=fig_post_process(
                create_goal_plot(goals_consumer.orange_goals, color="#db3e00")
            ),
        ),
        dcc.Graph(
            id="example-graph-4",
            figure=fig_post_process(
                create_disc_plot(disc_playing_consumer.disc_positions)
            ),
        ),
    ],
)


if __name__ == "__main__":
    app.run_server(debug=True)
