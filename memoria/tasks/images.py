import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from exifmwg import ExifTool
from exifmwg.models import ImageMetadata
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task
from huey.contrib.djhuey import lock_task

from memoria.imageops.index import handle_existing_image
from memoria.imageops.index import handle_new_image
from memoria.imageops.sync import fill_image_metadata_from_db
from memoria.models import Image as ImageModel
from memoria.models import ImageSource
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageUpdateTaskModel
from memoria.utils.constants import EXIF_TOOL_EXE

logger = logging.getLogger(__name__)


@db_task()
def sync_metadata_to_files(images: list[ImageModel]) -> None:
    """
    Syncs the metadata from the database to the image file for the given models

    Models are assumed to be dirty already
    """
    metadata_items = []
    for image in images:
        try:
            metadata = ImageMetadata(
                SourceFile=image.original_path,
                ImageHeight=image.height,
                ImageWidth=image.width,
            )

            updated = fill_image_metadata_from_db(image, metadata)

            if updated:
                metadata_items.append(metadata)

        except Exception:  # noqa: PERF203
            # Log the error with relevant image details
            logger.exception(f"Failed to process metadata for image {image.original_path}")

    if metadata_items:
        with ExifTool(EXIF_TOOL_EXE, encoding="utf8") as tool:
            tool.bulk_write_image_metadata(metadata_items)
        for image in images:
            image.update_hashes()
            image.mark_as_clean()


@db_task()
def index_image_batch(pkgs: list[ImageIndexTaskModel]) -> None:
    with ExifTool(EXIF_TOOL_EXE, encoding="utf8") as tool, transaction.atomic():
        for pkg in pkgs:
            if not pkg.logger:
                pkg.logger = logger

            pkg.logger.info(f"Indexing {pkg.image_path.stem}")

            # If no source, we use the parent folder name
            if not pkg.source:
                img_src, _ = ImageSource.objects.get_or_create(name=pkg.image_path.parent.name)
                pkg.source = img_src

                handle_new_image(pkg, tool)


@db_task()
def index_update_existing_images(pkgs: list[ImageUpdateTaskModel]) -> None:
    with transaction.atomic():
        for pkg in pkgs:
            if not pkg.logger:
                pkg.logger = logger

            pkg.logger.info(f"Checking {pkg.image_path.stem} for updates")

            handle_existing_image(pkg)


@db_periodic_task(crontab(minute="0", hour="0"))
@lock_task("trash-delete")
def remove_trashed_images() -> None:
    # Filter images based on deleted_at being less than now - some set period of time and call .delete on the queryset
    # TODO: Set the days from settings
    qs = ImageModel.objects.filter(deleted_at__lte=timezone.now() - timedelta(days=30))

    qs.delete()
