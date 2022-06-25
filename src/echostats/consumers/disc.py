from echostats.consumers import BaseConsumer
from echostats.models import ConsumerEvent
from echostats.models import Disc
from echostats.models import EchoEvent
from echostats.models import GameStatus
from echostats.models import Vector3D


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
