from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from django.db.models.query import QuerySet

from memoria.models import Image


@dataclass(slots=True)
class ImageIndexTaskModel:
    root_dir: Path
    image_path: Path
    hash_threads: int
    original_hash: str
    thumbnail_size: int
    large_image_size: int
    large_image_quality: int

    logger: Logger | None = None
    overwrite: bool = False
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None


@dataclass(slots=True)
class ImageUpdateTaskModel:
    root_dir: Path
    image_path: Path
    image: Image

    logger: Logger | None = None
    overwrite: bool = False
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None


@dataclass(slots=True)
class ImageReplaceTaskModel:
    root_dir: Path
    image: Image
    logger: Logger | None = None
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None
