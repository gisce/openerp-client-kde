"""
Session – value object that holds the current server connection parameters.

This is a pure-Python dataclass with no Qt or RPC dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SessionState(Enum):
    """Possible authentication states for a session."""
    DISCONNECTED = auto()
    LOGGED_IN = auto()
    ERROR = auto()
    INVALID_CREDENTIALS = auto()


@dataclass
class Session:
    """Immutable snapshot of connection + authentication data.

    Instances are created by the authentication use-case and passed
    to the RPC infrastructure layer.  They are *not* mutated in-place;
    create a new instance when the state changes.
    """

    url: str = ""
    database: str = ""
    username: str = ""
    uid: Optional[int] = None
    state: SessionState = SessionState.DISCONNECTED
    context: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    @property
    def is_logged_in(self) -> bool:
        return self.state == SessionState.LOGGED_IN

    @property
    def display_name(self) -> str:
        if self.is_logged_in:
            return f"{self.username}@{self.database}"
        return "(not logged in)"

    def with_credentials(
        self,
        url: str,
        database: str,
        username: str,
    ) -> "Session":
        """Return a *new* Session with updated connection parameters."""
        return Session(
            url=url,
            database=database,
            username=username,
            uid=None,
            state=SessionState.DISCONNECTED,
            context=self.context.copy(),
        )

    def authenticated(self, uid: int, context: Optional[dict] = None) -> "Session":
        """Return a *new* Session in the LOGGED_IN state."""
        return Session(
            url=self.url,
            database=self.database,
            username=self.username,
            uid=uid,
            state=SessionState.LOGGED_IN,
            context=context or self.context.copy(),
        )

    def failed(self, invalid_credentials: bool = False) -> "Session":
        """Return a *new* Session in an error state."""
        state = (
            SessionState.INVALID_CREDENTIALS
            if invalid_credentials
            else SessionState.ERROR
        )
        return Session(
            url=self.url,
            database=self.database,
            username=self.username,
            uid=None,
            state=state,
            context=self.context.copy(),
        )
