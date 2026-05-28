"""Time slot API — list Akiflow calendar blocks/time slots.

Akiflow exposes time slots through the same incremental-sync pattern used by
``/v5/tasks`` and ``/v5/labels``. A time slot represents a calendar block on the
Akiflow calendar. Tasks may reference a slot with ``time_slot_id``.

This module intentionally implements read support first. The public web API
surface for mutating time slots is undocumented and has not been verified.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import Akiflow


class TimeSlot:
    """Operations on Akiflow time slots, available as ``client.time_slot``.

    Akiflow's internal web API returns time slots from ``GET /v5/time_slots``.
    Responses follow the standard Akiflow sync shape:

    ``{"data": [...], "sync_token": "...", "has_next_page": false}``
    """

    def __init__(self, client: Akiflow):
        self._client = client

    def list(self, *, sync_token: str | None = None, limit: int = 2500) -> dict:
        """Fetch time slots, with optional incremental sync.

        Args:
            sync_token: Cursor from a previous ``list()`` response. Pass this
                to get only slots changed since the last call.
            limit: Max slots per page. Defaults to 2500, matching the web API
                usage observed in Akiflow clients.

        Returns:
            Dict with ``data`` (list of time-slot dicts), ``sync_token``
            cursor, and ``has_next_page``.
        """
        params: dict[str, Any] = {"limit": str(limit)}
        if sync_token:
            params["sync_token"] = sync_token
        return self._client._get("/v5/time_slots", params=params)

    def all(self, *, limit: int = 2500, max_pages: int = 1000) -> list[dict]:
        """Fetch all time slots by following Akiflow's sync-token cursor.

        Args:
            limit: Max slots per page.
            max_pages: Safety cap to avoid infinite loops if the API returns a
                non-advancing cursor.

        Returns:
            List of time-slot dictionaries.
        """
        slots: list[dict] = []
        cursor: str | None = None

        for _ in range(max_pages):
            response = self.list(sync_token=cursor, limit=limit)
            page = response.get("data") or []
            slots.extend(page)

            if response.get("has_next_page") is not True:
                break

            next_cursor = response.get("sync_token")
            if not next_cursor or next_cursor == cursor:
                break
            cursor = next_cursor

        return slots
