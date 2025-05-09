import logging
from pathlib import Path
from typing import Annotated

from django.core.paginator import Paginator
from django_typer.management import TyperCommand
from typer import Argument
from typer import Option

from memoria.models import Image as ImageModel
from memoria.tasks.images import index_replace_existing_images
from memoria.tasks.models import ImageReplaceTaskModel
from memoria.utils.constants import BATCH_SIZE
from memoria.utils.constants import IMAGE_EXTENSIONS

logger = logging.getLogger("memoria.replace")


class Command(TyperCommand):
    help = "Replaces Image(s) "

    def handle(
        self,
        top_level_dir: Annotated[
            Path,
            Option("--top-lvl-dir", help="Set the top level directory for folder structure"),
        ],
        paths: Annotated[list[Path], Argument(help="The paths to index for new images")],
        *,
        synchronous: Annotated[bool, Option(help="If True, run the indexing in the same process")] = True,
    ) -> None:
        all_image_paths: list[Path] = []
        for path in [x.resolve() for x in paths]:
            for extension in IMAGE_EXTENSIONS:
                all_image_paths.extend(list(path.rglob(f"*{extension}")))

        paginator = Paginator(
            ImageModel.objects.filter(original=all_image_paths).all(),
            BATCH_SIZE,
        )

        for i in paginator.page_range:
            batch: list[ImageReplaceTaskModel] = [
                ImageReplaceTaskModel(top_level_dir, image, logger=logger) for image in paginator.page(i).object_list
            ]
            if synchronous:
                index_replace_existing_images.call_local(batch)
            else:  # pragma: no cover
                index_replace_existing_images(batch)
