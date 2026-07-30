import logging
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    event_id: str
    humanitix_parameter: str
    wheel_parameter: str
    cloudfront_secret_parameter: str
    log_level: str = "INFO"

    @classmethod
    def load_settings(cls) -> "Settings":
        return cls(
            event_id=os.environ["EVENT_ID"],
            humanitix_parameter=os.environ["HUMANITIX_PARAMETER"],
            wheel_parameter=os.environ["WHEEL_PARAMETER"],
            cloudfront_secret_parameter=os.environ["CLOUDFRONT_SECRET_PARAMETER"],
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )

    def configure_logging(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            force=True,
        )
