from __future__ import annotations

import html
import json
import logging
import os
import random
import re
import smtplib
from email.message import EmailMessage
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import Settings
from humanitix import HumanitixClient
from secrets import Secrets
from util import wheel_title
from wheel import WheelClient

logger = logging.getLogger(__name__)

GMAIL_USERNAME = "andrew.j.humphrey@gmail.com"
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465

def _response(status_code: int, body: str, content_type: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }

def get_accept(event):
    # Lambda Function URL or API Gateway style
    headers = event.get("headers") or {}
    for key, value in headers.items():
        if key.lower() == "accept":
            return value if isinstance(value, str) else value.get("value", "")

    # CloudFront Lambda@Edge event shape
    try:
        cf_headers = event["Records"][0]["cf"]["request"]["headers"]
        values = cf_headers.get("accept", [])
        return values[0].get("value", "") if values else ""
    except (KeyError, IndexError, TypeError):
        return ""

def deduplicate_names(names: list[str]) -> tuple[list[str], list[str]]:
    """
    Remove duplicate names while preserving the first occurrence.
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


def requested_date(request) -> datetime.date | None:
    """
    Extract the requested event date from the Lambda Function URL.
        / -> next upcoming event
        /today -> today's event
        /2026-08-02 -> event on 2 August 2026
    """

    path = (
        request.get("rawPath")
        or request.get("path")
        or ""
    ).strip("/")

    if not path:
        return None

    if path.casefold() == "today":
        return "today"

    try:
        return datetime.strptime(
            path,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        raise ValueError(
            "Path must be /today or /YYYY-MM-DD"
        )


def is_eventbridge_scheduled_event(event: dict) -> bool:
    """Return whether *event* is an EventBridge schedule invocation."""

    return (
        event.get("source") in {"aws.events", "aws.scheduler"}
        and event.get("detail-type") == "Scheduled Event"
    )


def human_date(value: datetime) -> str:
    """Format a date as a human-friendly date with an ordinal day."""

    day = value.day
    suffix = "th" if 11 <= day % 100 <= 13 else {
        1: "st",
        2: "nd",
        3: "rd",
    }.get(day % 10, "th")
    return f"{day}{suffix} {value.strftime('%B %Y')}"


def weekday_name(now: datetime | None = None) -> str:
    """Return the current weekday in the schedule's Auckland timezone."""

    current_time = now or datetime.now(ZoneInfo("Pacific/Auckland"))
    return current_time.strftime("%A")





def send_email(subject, body, recipients_value, app_password):
    """
    Send an email via Gmail SMTP.
    Email is only sent when the EMAIL_RECIPIENTS environment variable
    is set to one or more email addresses.
    EMAIL_RECIPIENTS may contain multiple comma-separated addresses, e.g.:
    """

    if not recipients_value:
        return

    recipients = [
        address.strip()
        for address in recipients_value.split(",")
        if address.strip()
    ]

    if not recipients:
        return

    logger.info(f"Sending email to {recipients}")

    message = EmailMessage()
    message["From"] = GMAIL_USERNAME
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as smtp:
        smtp.login(GMAIL_USERNAME, app_password)
        smtp.send_message(message)


def lambda_handler(request, context):
    settings = Settings.load_settings()
    settings.configure_logging()

    raw_path = request.get("rawPath", "").lstrip("/")
    # Only allow "", "today" or YYYY-MM-DD
    if raw_path not in ["today", ""] and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_path):
        logger.info(f"Rejected request for {raw_path}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid date. Use YYYY-MM-DD or today."}),
        }

    logger.info("Starting Little Loop wheel generation")

    accept=get_accept(request)

    wants_json = is_eventbridge_scheduled_event(request) or "application/json" in accept

    secrets = Secrets()

    try:
        target_date = requested_date(request)

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

            humanitix_event = humanitix.get_event(
                settings.event_id
            )
            if target_date == "today":
                tz = ZoneInfo(humanitix_event.timezone)
                target_date = datetime.now(tz).date()

            logger.info("target_date = %s", target_date)


            if target_date is None:
                logger.info(
                    "Selecting next upcoming event"
                )

                event_date = humanitix.find_next_event_date(
                    humanitix_event
                )

            else:
                logger.info(
                    "Selecting event on %s",
                    target_date.isoformat(),
                )

                event_date = humanitix.find_event_date(
                    humanitix_event,
                    target_date,
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

        if is_eventbridge_scheduled_event(request):
            send_email(
                subject="Wheel link for today",
                body=f"Hi and happy {weekday_name()}\nThe wheel for the {human_date(event_date.start_date)} little loop has been generated, the URL is {url}, so far {len(names)} people have signed up.\nKind regards,\nEarly Bird Run Crew.",
                recipients_value=os.environ.get("EMAIL_RECIPIENTS", "").strip(),
                app_password=secrets.get_secret("/littleloop/email-key"),
            )
        else:
            logger.info(
                "Skipping email for a non-scheduled invocation"
            )
        result = {
            "requested_date": target_date.isoformat() if target_date else "next",
            "event_date_display": wheel_title(event_date.start_date),
            "wheel_url": url,
            "attendee_count": len(names),
            "original_ticket_count": len(original_names),
            "duplicates_removed": duplicates_removed,
        }

        if wants_json:
            logger.info("Returning JSON")
            return _response(
                200,
                json.dumps(result),
                "application/json",
            )

        safe_url = html.escape(url, quote=True)
        safe_title = html.escape(wheel_title(event_date.start_date))

        return _response(
            200,
            f"""<!doctype html>
        <html>
          <head><meta charset="utf-8"><title>Event details</title></head>
          <body>
            <p>Requested date: {html.escape(target_date.isoformat() if target_date else "next")}</p>
            <p>Event: {safe_title}</p>
            <p><a href="{safe_url}">{safe_url}</a></p>
            <p>Attendees: {len(names)}</p>
            <p>Original tickets: {len(original_names)}</p>
            <p>Duplicates removed: {duplicates_removed}</p>
          </body>
        </html>""", "text/html; charset=utf-8")

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
