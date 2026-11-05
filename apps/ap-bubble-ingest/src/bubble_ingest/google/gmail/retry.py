"""Retries Gmail calls with backoff while Google rate limits them or fails temporarily.

Gmail allows 6,000 quota units per user and minute (a full message costs 60), and answers
403 rateLimitExceeded when the minute is used up, without a Retry-After header.
"""

import random
import time
from collections.abc import Callable

import requests

from bubble_core.log import get_logger

MAX_ATTEMPTS = 8
_MAX_DELAY_SECONDS = 32.0  # the quota window is a minute; 2+4+...+32 s waits it out
_HTTP_FORBIDDEN = 403
_HTTP_TOO_MANY_REQUESTS = 429
_HTTP_SERVER_ERROR = 500
_RATE_LIMIT_REASONS = {"rateLimitExceeded", "userRateLimitExceeded"}

logger = get_logger(__name__)


def with_retry[T](call: Callable[[], T]) -> T:
    """Run call; on a transient error, wait (exponential backoff, jitter) and run it again."""
    for attempt in range(1, MAX_ATTEMPTS):
        try:
            return call()
        except requests.RequestException as error:
            if not _is_transient(error):
                raise
            _wait(attempt, error)
    return call()


def _is_transient(error: requests.RequestException) -> bool:
    if isinstance(error, requests.ConnectionError | requests.Timeout):
        return True
    response = error.response
    if response is None:
        return False
    return response.status_code >= _HTTP_SERVER_ERROR or _is_rate_limit(response)


def _is_rate_limit(response: requests.Response) -> bool:
    if response.status_code == _HTTP_TOO_MANY_REQUESTS:
        return True
    return response.status_code == _HTTP_FORBIDDEN and _reason_of(response) in _RATE_LIMIT_REASONS


def _reason_of(response: requests.Response) -> str | None:
    try:
        return response.json()["error"]["errors"][0]["reason"]
    except (ValueError, LookupError, TypeError):
        return None


def _wait(attempt: int, error: requests.RequestException) -> None:
    """Sleep before the next attempt; rate limits are routine here, other failures are not."""
    delay = min(2.0**attempt, _MAX_DELAY_SECONDS) + random.random()
    response = error.response
    if response is not None and _is_rate_limit(response):
        logger.debug("Gmail rate limit reached; retry %d in %.1fs", attempt, delay)
    else:
        cause = response.status_code if response is not None else type(error).__name__
        logger.warning("Gmail call failed (%s); retry %d in %.1fs", cause, attempt, delay)
    time.sleep(delay)
