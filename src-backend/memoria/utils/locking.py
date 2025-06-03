import logging
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

logger = logging.getLogger(__name__)


@contextmanager
def file_lock_with_cleanup(lock_path: Path, timeout: int | float = 5.0):
    lock = FileLock(lock_path)

    try:
        with lock.acquire(timeout=timeout):
            yield
    except TimeoutError:
        logger.warning(f"Lock timeout after {timeout}s, attempting stale lock cleanup")

        try:
            if lock_path.exists():
                lock_path.unlink()
                logger.debug(f"Removed stale lock: {lock_path}")

            # Retry with the same timeout
            with lock.acquire(timeout=timeout):
                logger.debug(f"Successfully acquired {lock_path} after cleanup")
                yield

        except (OSError, PermissionError) as e:
            logger.exception("Failed to remove stale lock")
            raise TimeoutError("Could not acquire lock after cleanup") from e  # noqa: EM101, TRY003
