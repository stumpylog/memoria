from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from django.db.models.query import QuerySet

from memoria.models import Image
from memoria.models import ImageSource


@dataclass(slots=True)
class ImageIndexTaskModel:
    image_path: Path
    hash_threads: int
    original_hash: str
    logger: Logger | None = None
    source: ImageSource | None = None
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None


@dataclass(slots=True)
class ImageUpdateTaskModel:
    image_path: Path
    image: Image
    logger: Logger | None = None
    source: ImageSource | None = None
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None
