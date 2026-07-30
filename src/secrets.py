from functools import lru_cache

import boto3


class Secrets:
    """
    Simple wrapper around AWS Systems Manager Parameter Store.

    Values are cached for the lifetime of the Lambda execution environment
    to avoid repeated API calls on warm invocations.
    """

    def __init__(self):
        self._ssm = boto3.client("ssm")

    @lru_cache(maxsize=32)
    def get_secret(self, parameter_name: str) -> str:
        response = self._ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )

        return response["Parameter"]["Value"]


_default = Secrets()


def get_secret(parameter_name: str) -> str:
    """
    Backwards-compatible helper.

    Existing code can simply call:

        get_secret("/littleloop/humanitix/api-key")
    """
    return _default.get_secret(parameter_name)
