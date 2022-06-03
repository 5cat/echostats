from __future__ import annotations

import ipaddress
import uuid
from datetime import datetime as datetime_class
from datetime import timedelta
from enum import Enum
from typing import Any
from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field
from pydantic import StrictBytes
from pydantic import StrictStr
from pydantic import validator


class MapName(Enum):
    MPL_ARENA_A = "mpl_arena_a"
    MPL_LOBBY_B2 = "mpl_lobby_b2"
    MPL_COMBAT_DYSON = "mpl_combat_dyson"
    MPL_COMBAT_COMBUSTION = "mpl_combat_combustion"
    MPL_COMBAT_FISSION = "mpl_combat_fission"
    MPL_COMBAT_GAUSS = "mpl_combat_gauss"
    INVALID_LEVEL = "INVALID LEVEL"


class MatchType(Enum):
    ECHO_ARENA_PRIVATE = "Echo_Arena_Private"
    ECHO_ARENA = "Echo_Arena"
    ECHO_COMBAT = "Echo_Combat"
    ECHO_COMBAT_PRIVATE = "Echo_Combat_Private"
    SOCIAL_2_0 = "Social_2.0"
    INVALID_GAME_TYPE = "INVALID GAMETYPE"


class GameStatus(Enum):
    PRE_MATCH = "pre_match"
    ROUND_START = "round_start"
    PLAYING = "playing"
    SCORE = "score"
    ROUND_OVER = "round_over"
    POST_MATCH = "post_match"
    PRE_SUDDEN_DEATH = "pre_sudden_death"
    SUDDEN_DEATH = "sudden_death"
    POST_SUDDEN_DEATH = "post_sudden_death"


class PausedState(Enum):
    UN_PAUSED = "unpaused"
    UN_PAUSING = "unpausing"
    PAUSED = "paused"
    PAUSED_REQUESTED = "paused_requested"


class TeamEnum(Enum):
    ORANGE = "orange"
    BLUE = "blue"


class GoalType(Enum):
    NO_GOAL = "[NO GOAL]"
    INVALID = "[INVALID]"
    SLAM_DUNK = "SLAM DUNK"
    INSIDE_SHOT = "INSIDE SHOT"
    LONG_SHOT = "LONG SHOT"
    BOUNCE_SHOT = "BOUNCE SHOT"
    LONG_BOUNCE_SHOT = "LONG BOUNCE SHOT"
    SELF_GOAL = "SELF GOAL"
    BUMPER_SHOT = "BUMPER SHOT"


class Pause(BaseModel):
    paused_state: Optional[PausedState]
    unpaused_team: Optional[TeamEnum]
    paused_requested_team: Optional[TeamEnum]
    unpaused_timer: timedelta
    paused_timer: timedelta

    @validator("paused_state", "unpaused_team", "paused_requested_team", pre=True)
    def __convert_str_none_into_none(cls, v: Optional[str]) -> Optional[str]:
        return None if v == "none" else v


class Throw(BaseModel):
    arm_speed: float
    total_speed: float
    off_axis_spin_deg: float
    wrist_throw_penalty: float
    rot_per_sec: float
    pot_speed_from_rot: float
    speed_from_arm: float
    speed_from_movement: float
    speed_from_wrist: float
    wrist_align_to_throw_deg: float
    throw_align_to_movement_deg: float
    off_axis_penalty: float
    throw_move_penalty: float


class LastScore(BaseModel):
    disc_speed: float
    team: TeamEnum
    goal_type: GoalType
    point_amount: Literal[2, 3]
    distance_thrown: float
    person_scored: str
    assist_scored: str


class Vector3D(BaseModel):
    x: float
    y: float
    z: float


class PFLU(BaseModel):
    position: Vector3D
    forward: Vector3D
    left: Vector3D
    up: Vector3D

    @validator("position", "forward", "left", "up", pre=True)
    def __convert_list_to_vector3d(cls, v: list[float]) -> dict:
        return {"x": v[0], "y": v[1], "z": v[2]}


class Disc(PFLU):
    velocity: Vector3D
    bounce_count: int

    @validator("velocity", pre=True)
    def __convert_list_to_vector3d(cls, v: list[float]) -> dict:
        return {"x": v[0], "y": v[1], "z": v[2]}


class Stats(BaseModel):
    points: int
    possession_time: timedelta
    interceptions: int
    blocks: int
    steals: int
    catches: int
    passes: int
    saves: int
    goals: int
    stuns: int
    assists: int
    shots_taken: int


class Player(BaseModel):
    name: str
    playerid: int
    userid: int
    number: int
    level: int
    ping: int
    stunned: bool
    invulnerable: bool
    possession: bool
    holding_left: Any
    holding_right: Any
    blocking: bool
    stats: Stats
    velocity: Vector3D
    head: PFLU
    body: PFLU
    rhand: PFLU
    lhand: PFLU

    @validator("rhand", "lhand", pre=True)
    def __replace_pos_with_position(
        cls, v: Optional[dict[str, float]]
    ) -> Optional[dict[str, float]]:
        if v is None:
            return v
        else:
            v["position"] = v.pop("pos")
            return v

    @validator("velocity", pre=True)
    def __convert_list_to_vector3d(cls, v: list[float]) -> dict:
        return {"x": v[0], "y": v[1], "z": v[2]}


class Possession(BaseModel):
    team: Optional[int]
    player: Optional[int]


class Team(BaseModel):
    name: str = Field(alias="team")
    possession: Optional[bool]
    stats: Optional[Stats]
    players: Optional[list[Player]]


class EchoEvent(BaseModel):
    client_name: Optional[str]
    sessionid: Optional[uuid.UUID]
    sessionip: Optional[ipaddress.IPv4Address]

    match_type: Optional[MatchType]
    map_name: Optional[MapName]

    game_clock: Optional[timedelta]
    game_clock_display: Optional[str]

    private_match: Optional[bool]
    total_round_count: Optional[int]

    blue_round_score: Optional[int]
    orange_round_score: Optional[int]

    blue_points: Optional[int]
    orange_points: Optional[int]

    tournament_match: Optional[bool]

    blue_team_restart_request: Optional[bool]
    orange_team_restart_request: Optional[bool]

    right_shoulder_pressed: Optional[float]
    right_shoulder_pressed2: Optional[float]

    left_shoulder_pressed: Optional[float]
    left_shoulder_pressed2: Optional[float]

    packet_loss_ratio: Optional[Any]

    game_status: Optional[GameStatus]

    pause: Optional[Pause]

    last_throw: Optional[Throw]

    last_score: Optional[LastScore]

    disc: Optional[Disc]

    player: Optional[PFLU]

    teams: list[Team]

    possession: Optional[Possession]

    err_description: Optional[str]
    err_code: Optional[int]

    @validator("game_status", pre=True)
    def __replace_empty_string_with_none(cls, v: Optional[str]) -> Optional[str]:
        return None if v == "" else v

    @validator("possession", pre=True)
    def __parse_possession(cls, v: Optional[tuple[int, int]]) -> Optional[dict]:
        if v is None:
            return v
        team, player = v
        return {
            "team": None if team == -1 else team,
            "player": None if player == -1 else player,
        }

    @validator("last_score", pre=True)
    def __remove_if_there_is_no_last_goal(cls, v: Optional[dict]) -> Optional[dict]:
        if v.get("point_amount", 0) == 0:
            return None
        else:
            return v

    @validator("player", pre=True)
    def __remove_vr_prefix(
        cls, v: Optional[dict[str, float]]
    ) -> Optional[dict[str, float]]:
        if v is None:
            return v
        else:
            new_v = dict()
            for key, value in v.items():
                new_v[key.replace("vr_", "")] = value
            return new_v

    @validator("err_code", pre=True)
    def __remove_if_is_equal_to_zero(cls, v: Optional[int]) -> Optional[int]:
        return None if v == 0 else v


class StreamEvent(BaseModel):
    data: StrictStr | StrictBytes
    datetime: datetime_class = Field(
        default_factory=lambda: datetime_class.now().isoformat(
            sep=" ", timespec="milliseconds"
        )
    )


class ConsumerEvent(BaseModel):
    stream_event: StreamEvent
    echo_event: EchoEvent
