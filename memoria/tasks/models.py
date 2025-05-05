from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from django.db.models.query import QuerySet

from memoria.models import Image


@dataclass(slots=True)
class ImageIndexTaskModel:
    parent_path: Path
    image_path: Path
    hash_threads: int
    original_hash: str

    logger: Logger | None = None
    overwrite: bool = False
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None


@dataclass(slots=True)
class ImageUpdateTaskModel:
    parent_path: Path
    image_path: Path
    image: Image

    logger: Logger | None = None
    overwrite: bool = False
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None
