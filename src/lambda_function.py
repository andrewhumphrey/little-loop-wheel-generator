from __future__ import annotations

import json
import logging
import random

from config import Settings
from humanitix import HumanitixClient
from secrets import Secrets
from util import wheel_title
from wheel import WheelClient


logger = logging.getLogger(__name__)


def _response(
    status_code: int,
    body: dict,
) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
        },
        "body": json.dumps(body),
    }


def deduplicate_names(names: list[str]) -> tuple[list[str], list[str]]:
    """
    Remove duplicate names while preserving the first occurrence.

    Returns:
        (
            unique_names,
            duplicate_names_removed
        )
    """

    seen = set()
    unique_names = []
    duplicates = []

    for name in names:
        normalised = name.strip()

        if not normalised:
            continue

        key = normalised.casefold()

        if key in seen:
            duplicates.append(normalised)
            continue

        seen.add(key)
        unique_names.append(normalised)

    return unique_names, duplicates


def lambda_handler(event, context):
    """
    Lambda Function URL entry point.

    Returns:
        {
            "wheel_url": "...",
            "attendee_count": 10,
            "duplicates_removed": [
                "John Smith"
            ]
        }
    """

    settings = Settings.load_settings()
    settings.configure_logging()

    logger.info(
        "Starting Little Loop wheel generation"
    )

    secrets = Secrets()

    try:
        humanitix_api_key = secrets.get_secret(
            settings.humanitix_parameter
        )

        wheel_api_key = secrets.get_secret(
            settings.wheel_parameter
        )

        with HumanitixClient(
            humanitix_api_key
        ) as humanitix:

            logger.info(
                "Fetching event %s",
                settings.event_id,
            )

            event = humanitix.get_event(
                settings.event_id
            )

            event_date = humanitix.find_next_event_date(
                event
            )

            logger.info(
                "Using event date %s",
                event_date.id,
            )

            tickets = humanitix.get_all_tickets(
                settings.event_id,
                event_date.id,
            )

        original_names = [
            ticket.full_name.strip().title()
            for ticket in tickets
            if ticket.full_name
        ]

        names, duplicates_removed = deduplicate_names(
            original_names
        )

        random.shuffle(names)

        logger.info(
            "Original attendees: %s",
            len(original_names),
        )

        logger.info(
            "Unique wheel entries: %s",
            len(names),
        )

        logger.info(
            "Duplicates removed: %s",
            duplicates_removed,
        )

        if not names:
            raise RuntimeError(
                "No attendee names found"
            )

        with WheelClient(
            wheel_api_key
        ) as wheel:

            url = wheel.create_shared_wheel(
                names,
                title=wheel_title(event_date.start_date),
            )

        logger.info(
            "Generated wheel: %s",
            url,
        )

        return _response(
            200,
            {
                "event_date_display": event_date.start_date.strftime(
                    "%A %d %B %Y %H:%M %Z"
                ),
                "wheel_url": url,
                "attendee_count": len(names),
                "original_ticket_count": len(original_names),
                "duplicates_removed": duplicates_removed,
            },
        )

    except Exception as exc:
        logger.exception(
            "Failed generating wheel"
        )

        return _response(
            500,
            {
                "error": str(exc),
            },
        )
