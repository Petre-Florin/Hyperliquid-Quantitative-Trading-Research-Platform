"""Small retry/backoff helper for flaky network calls."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger("retry")

T = TypeVar("T")


async def retry_with_backoff(
    fn: Callable[[], Awaitable[T]],
    max_attempts: int = 5,
    base_delay: float = 1.0,
) -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except Exception as e:
            if attempt == max_attempts:
                logger.error("Giving up after %d attempts: %s", max_attempts, e)
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Attempt %d/%d failed (%s), retrying in %.1fs",
                attempt, max_attempts, e, delay,
            )
            await asyncio.sleep(delay)

    raise RuntimeError("unreachable")