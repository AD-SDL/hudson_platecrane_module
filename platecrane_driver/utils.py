from contextlib import contextmanager
from enum import IntEnum
from threading import Lock
from typing import Iterator, TypeVar

GenericIntEnum = TypeVar("GenericIntEnum", bound=IntEnum)


@contextmanager
def lock_threading_lock(lock: Lock, *, timeout: float) -> Iterator[None]:
    """Context manager for using a `threading.lock` with a timeout"""
    if not timeout > 0:
        raise ValueError("Timeout must be positive")

    if not lock.acquire(timeout=timeout):
        raise TimeoutError(f"Could not acquire lock after {timeout} seconds")

    try:
        yield
    finally:
        lock.release()
