import sys
import time
from functools import wraps


def retry(exceptions, attempts=3, delay=1.0, backoff=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as error:
                    if attempt == attempts:
                        raise
                    print(
                        f"Tentative {attempt}/{attempts} échouée ({error}), "
                        f"nouvel essai dans {wait}s",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                    wait *= backoff

        return wrapper

    return decorator
