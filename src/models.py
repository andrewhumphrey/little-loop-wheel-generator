from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class EventDate:
    id: str
    start_date: datetime


@dataclass(frozen=True)
class Ticket:
    first_name: str
    last_name: str
    organisation: str
    ticket_type: str
    status: str
    order_name: str
    event_date_id: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Ticket":
        return cls(
            first_name=data.get("firstName", "").strip(),
            last_name=data.get("lastName", "").strip(),
            organisation=data.get("organisation", ""),
            ticket_type=data.get("ticketTypeName", ""),
            status=data.get("status", ""),
            order_name=data.get("orderName", ""),
            event_date_id=data.get("eventDateId", ""),
        )


@dataclass(frozen=True)
class Event:
    id: str
    name: str
    dates: list[EventDate]
    timezone: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Event":
        dates = data.get("eventDates") or data.get("dates") or []

        parsed_dates: list[EventDate] = []

        for d in dates:
            if d.get("disabled") or d.get("deleted"):
                continue

            value = d.get("startDate")
            if not value:
                continue

            try:
                start = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
            except ValueError:
                continue

            parsed_dates.append(
                EventDate(
                    id=d.get("_id") or d.get("id"),
                    start_date=start,
                )
            )

        return cls(
            id=data.get("_id") or data.get("id"),
            name=data.get("name", ""),
            dates=parsed_dates,
            timezone=data.get("timezone", "UTC"),
        )
