from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from django.contrib.auth.models import Group

from memoria.models import ImageSource


@dataclass(slots=True)
class ImageIndexTaskModel:
    image_path: Path
    hash_threads: int = 4
    source: ImageSource | None = None
    view_groups: list[Group] | None = None
    edit_groups: list[Group] | None = None
    logger: Logger | None = None
