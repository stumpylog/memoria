from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from django.db.models.query import QuerySet

from memoria.models import ImageSource


@dataclass(slots=True)
class ImageIndexTaskModel:
    image_path: Path
    hash_threads: int = 4
    source: ImageSource | None = None
    view_groups: QuerySet | None = None
    edit_groups: QuerySet | None = None
    logger: Logger | None = None
