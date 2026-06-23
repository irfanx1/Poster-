"""
Lightweight in-memory session manager.

Each user moving through the search -> select -> title -> poster -> generate
flow has a single UserSession tracked here, keyed by user_id. No database is
used since sessions are short-lived; swap this for Redis/SQLite easily if you
need persistence across bot restarts.
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class Step(Enum):
    IDLE = auto()
    SELECT_RESULT = auto()
    TITLE_CHOICE = auto()
    AWAIT_CUSTOM_TITLE = auto()
    TEMPLATE_CHOICE = auto()
    POSTER_CHOICE = auto()
    AWAIT_CUSTOM_POSTER = auto()
    GENERATING = auto()


@dataclass
class UserSession:
    step: Step = Step.IDLE
    query: str = ""
    results: list = field(default_factory=list)
    page: int = 0
    selected: dict = field(default_factory=dict)   # full anime detail dict
    title: str = ""
    poster_path: str = ""
    template: str = "gen5"                         # selected template id; never falls back silently


class SessionManager:
    def __init__(self):
        self._sessions: dict[int, UserSession] = {}

    def get(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession()
        return self._sessions[user_id]

    def reset(self, user_id: int) -> None:
        self._sessions[user_id] = UserSession()


sessions = SessionManager()
