import logging
from pathlib import Path
from typing import Annotated
from typing import Final
from typing import Optional

from django_typer.management import TyperCommand
from typer import Argument
from typer import Option

from memoria.models import ImageSource
from memoria.tasks.images import index_single_image
from memoria.tasks.models import ImageIndexTaskModel


class Command(TyperCommand):
    help = "Indexes the given path(s) for new Images"

    IMAGE_EXTENSIONS: Final[set[str]] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".tif",
        ".webp",
    }

    def handle(
        self,
        paths: Annotated[list[Path], Argument(help="The paths to index for new images")],
        hash_threads: Annotated[int, Option(help="Number of threads to use for hashing")] = 4,
        source: Annotated[
            Optional[str],  # noqa: UP007
            Option(help="The source of the images to attach to the image"),
        ] = None,
        *,
        synchronous: Annotated[bool, Option(help="If True, run the indexing in the same process")] = True,
    ) -> None:
        logger = logging.getLogger(__name__)

        if source:
            img_src, created = ImageSource.objects.get_or_create(name=source)
            if created:
                logger.info(f"Created new source {source}")
            else:
                logger.info(f"Using existing source {source} (#{img_src.pk})")
        else:
            img_src = None

        self.image_paths: list[Path] = []

        for path in paths:
            for extension in self.IMAGE_EXTENSIONS:
                for filename in path.glob(f"**/*{extension}"):
                    self.image_paths.append(filename.resolve())

        logger.info(f"Found {len(self.image_paths)} images to index")

        for image_path in sorted(self.image_paths):
            pkg = ImageIndexTaskModel(image_path, hash_threads, img_src, logger)
            if synchronous:
                index_single_image.call_local(pkg)
            else:  # pragma: no cover
                index_single_image(pkg)
