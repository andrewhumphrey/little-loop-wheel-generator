from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from util import wheel_description
from wheel_logo import LOGO_DATA_URI


WHEEL_API_URL = "https://wheelofnames.com/api/v3/wheels"


class WheelClient:
    """
    Client wrapper for the Wheel of Names API.
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        debug: bool = False,
    ):
        self._debug = debug

        self._client = httpx.Client(
            timeout=timeout,
            http2=True,
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "x-api-key": api_key,
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WheelClient":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> None:
        self.close()

    def create_shared_wheel(
        self,
        names: list[str],
        *,
        title: str,
        description: str | None = None,
    ) -> str:
        """
        Creates a shared Wheel of Names wheel.

        Returns:
            Public wheel URL.
        """

        if description is None:
            description = wheel_description(datetime.now())

        payload = self._build_payload(
            names=names,
            title=title,
            description=description,
        )

        response = self._client.post(
            WHEEL_API_URL,
            json=payload,
        )

        if self._debug:
            print(
                "Wheel response:",
                response.status_code,
                response.text,
            )

        response.raise_for_status()

        data = response.json()

        try:
            path = data["data"]["path"]
        except KeyError as exc:
            raise RuntimeError(
                f"Unexpected Wheel API response: {data}"
            ) from exc

        return f"https://wheelofnames.com/{path}"

    @staticmethod
    def _build_payload(
        *,
        names: list[str],
        title: str,
        description: str,
    ) -> dict[str, Any]:
        return {
            "title": title,
            "description": description,
            "shareMode": "copyable",
            "wheelConfigs": [
                {
                    "entries": [
                        {
                            "text": name,
                        }
                        for name in names
                    ],
                    "pageBackgroundColor": "#ED1D2D",
                    "description": description,
                    "animateWinner": True,
                    "winnerMessage": "Who's a lucky Little Looper?",
                    "title": title,
                    "afterSpinSoundVolume": 100,
                    "hubSize": "L",
                    "customPictureDataUri": LOGO_DATA_URI,
                    "afterSpinSound": "carnival-shout",
                    "colorSettings": [
                        {
                            "color": "#ED1D2D",
                            "enabled": True,
                        },
                        {
                            "color": "#FFFFFF",
                            "enabled": True,
                        },
                        {
                            "color": "#000000",
                            "enabled": True,
                        },
                    ],
                    "pictureType": "uploaded",
                    "allowDuplicates": True,
                    "pointerChangesColor": False,
                    "pageGradient": False,
                }
            ],
        }
