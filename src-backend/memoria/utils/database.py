import random
import time

from django.db import IntegrityError
from django.db import models
from django.db import transaction


def get_or_create_robust(cls: type[models.Model], max_retries: int = 3, **kwargs):
    """
    Robust get_or_create that handles race conditions with exponential backoff

    This is a problem if multiple workers are trying to create the same record at once

    # TODO: There has to be a database method to handle this better
    """
    for attempt in range(max_retries + 1):
        try:
            # Try to get existing record first
            return cls.objects.get(**kwargs), False  # type: ignore
        except cls.DoesNotExist:  # type: ignore # noqa: PERF203
            try:
                # Use atomic transaction for create
                with transaction.atomic():
                    obj = cls.objects.create(**kwargs)  # type: ignore
                    return obj, True
            except IntegrityError:
                # Another worker created it between our get and create
                if attempt == max_retries:
                    # Last attempt - just return the existing one
                    return cls.objects.get(**kwargs), False  # type: ignore
                # Exponential backoff with jitter
                delay = ((2**attempt) * 0.1) + random.uniform(0, 0.1)  # noqa: S311
                time.sleep(delay)
                continue

    # Fallback - should never reach here
    return cls.objects.get(**kwargs), False  # type: ignore
