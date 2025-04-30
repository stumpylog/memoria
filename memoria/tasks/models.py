from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from memoria.models import ImageSource


@dataclass(slots=True)
class ImageIndexTaskModel:
    image_path: Path
    hash_threads: int = 4
    source: ImageSource | None = None
    logger: Logger | None = None
