import logging
import random
import time
from typing import Any
from typing import TypeVar

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db import connection
from django.db import models
from django.db import transaction

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=models.Model)


def _should_use_locking() -> bool:
    """
    Determine if the current database backend supports SELECT FOR UPDATE effectively.
    """
    backend_name = connection.vendor

    # Databases with good SELECT FOR UPDATE support
    if backend_name in ("postgresql", "mysql", "oracle"):
        return True

    # SQLite has limited support and can cause issues
    if backend_name == "sqlite":
        return False

    # Unknown database - default to no locking to be safe
    logger.warning(f"Unknown database backend '{backend_name}', disabling locking")
    return False


def get_or_create_robust(
    cls: type[T],
    max_retries: int = 3,
    use_locking: bool | None = None,
    **kwargs: Any,
) -> tuple[T, bool]:
    """
    Robust get_or_create that handles race conditions from parallel workers.

    Args:
        cls: Django model class
        max_retries: Maximum number of retry attempts
        use_locking: Whether to use SELECT FOR UPDATE (None = auto-detect)
        **kwargs: Fields to match/create the object with

    Returns:
        Tuple of (object, created_flag)

    Raises:
        Exception: If all retry attempts fail
    """
    last_exception = None

    # Auto-detect locking support if not specified
    if use_locking is None:
        use_locking = _should_use_locking()

    for attempt in range(max_retries + 1):
        try:
            if use_locking:
                return _get_or_create_with_locking(cls, **kwargs)
            return _get_or_create_without_locking(cls, **kwargs)

        except IntegrityError as e:
            last_exception = e
            logger.info(
                f"IntegrityError on attempt {attempt + 1}/{max_retries + 1} for {cls.__name__}: {e}",
            )

            # Try to fetch the record that was created by another worker
            try:
                obj = cls.objects.get(**kwargs)
                return obj, False
            except ObjectDoesNotExist:
                # Record disappeared - continue retrying
                pass

        except Exception as e:
            last_exception = e
            logger.error(
                f"Unexpected error on attempt {attempt + 1}/{max_retries + 1} for {cls.__name__}: {e}",
            )

        # Don't sleep on the last attempt
        if attempt < max_retries:
            # Exponential backoff with jitter
            delay = ((2**attempt) * 0.1) + random.uniform(0, 0.1)
            time.sleep(delay)

    # All attempts failed
    raise Exception(
        f"Failed to get_or_create {cls.__name__} after {max_retries + 1} attempts. Last error: {last_exception}",
    )


def _get_or_create_with_locking(cls: type[T], **kwargs: Any) -> tuple[T, bool]:
    """
    Get or create using SELECT FOR UPDATE to prevent race conditions.
    """
    with transaction.atomic():
        # Try to get existing record with row lock
        try:
            obj = cls.objects.select_for_update().get(**kwargs)
            return obj, False
        except ObjectDoesNotExist:
            # No existing record - create new one
            # The transaction and previous lock should prevent most race conditions
            obj = cls.objects.create(**kwargs)
            return obj, True


def _get_or_create_without_locking(cls: type[T], **kwargs: Any) -> tuple[T, bool]:
    """
    Get or create without locking - fallback for databases that don't support it.
    """
    try:
        obj = cls.objects.get(**kwargs)
        return obj, False
    except ObjectDoesNotExist:
        # Use atomic transaction for create
        with transaction.atomic():
            obj = cls.objects.create(**kwargs)
            return obj, True
