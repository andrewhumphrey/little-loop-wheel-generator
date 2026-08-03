from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from models import Event, EventDate, Ticket

HUMANITIX_BASE_URL = "https://api.humanitix.com/v1"


class HumanitixClient:
    """
    Thin wrapper around the Humanitix REST API.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        debug: bool = False,
    ):
        self._api_key = api_key
        self._debug = debug
        self._client = httpx.Client(
            base_url=HUMANITIX_BASE_URL,
            timeout=timeout,
            http2=True,
            headers={
                "accept": "application/json",
                "x-api-key": api_key,
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HumanitixClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    #
    # Internal helper
    #

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._client.get(path, params=params)

        if self._debug:
            print(f"{response.request.method} {response.request.url}")
            print(response.status_code)

        response.raise_for_status()

        return response.json()

    #
    # Public API
    #

    def get_event(self, event_id: str) -> Event:
        data = self._get(f"/events/{event_id}")
        return Event.from_api(data)

    def find_event_date(
        self,
        event: Event,
        target_date: date,
    ) -> EventDate:
        """
        Returns the event occurring on the supplied calendar date.
        """

        for event_date in event.dates:
            if event_date.start_date.date() == target_date:
                return event_date

        raise ValueError(
            f"No event found on {target_date.isoformat()}"
        )

    def find_next_event_date(self, event: Event) -> EventDate:
        """
        Returns the next upcoming event date.
        If there are no future dates, returns the most recent past date.
        """

        if not event.dates:
            raise ValueError("Event contains no event dates.")

        now = datetime.now(timezone.utc)

        future = [
            d
            for d in event.dates
            if d.start_date >= now
        ]

        if future:
            future.sort(key=lambda d: d.start_date)
            return future[0]

        past = sorted(
            event.dates,
            key=lambda d: d.start_date,
            reverse=True,
        )

        return past[0]

    def get_tickets(
        self,
        event_id: str,
        event_date_id: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[list[Ticket], int]:
        data = self._get(
            f"/events/{event_id}/tickets",
            params={
                "page": page,
                "pageSize": page_size,
                "eventDateId": event_date_id,
            },
        )

        tickets = [
            Ticket.from_api(ticket)
            for ticket in data.get("tickets", [])
        ]

        total = data.get("total", len(tickets))

        return tickets, total

    def get_all_tickets(
        self,
        event_id: str,
        event_date_id: str,
        *,
        page_size: int = 100,
    ) -> list[Ticket]:
        """
        Retrieves every ticket for an event date by following the
        Humanitix pagination API.
        """

        page = 1
        tickets: list[Ticket] = []

        while True:
            batch, total = self.get_tickets(
                event_id,
                event_date_id,
                page=page,
                page_size=page_size,
            )

            tickets.extend(batch)

            if len(tickets) >= total or not batch:
                break

            page += 1

        return tickets
