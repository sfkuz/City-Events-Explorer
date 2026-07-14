import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

logger = logging.getLogger(__name__)

def with_retry():
    return retry(
        stop = stop_after_attempt(5),
        wait = wait_exponential(multiplier=1, min=2, max=10),
        retry = retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before = lambda retry_state: logger.warning(
            f'Retrying attempt {retry_state.attempt_number} due to {retry_state.outcome.exception()}'
        )
    )