import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import httpx

logger = logging.getLogger(__name__)

def with_retry():
    return retry(
        stop = stop_after_attempt(3),
        wait = wait_fixed(2.0),
        retry = retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        before_sleep = lambda retry_state: logger.warning(
            f'Network error: {retry_state.outcome.exception()}'
            f'Retrying in {retry_state.next_action.sleep}'
            f'Attempt {retry_state.attempt_number}'
        )
    )