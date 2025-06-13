import logging
from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from exifmwg import ImageMetadata
from exifmwg import write_metadata
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from huey.contrib.djhuey import db_task
from huey.contrib.djhuey import lock_task

from memoria.imageops.index import handle_moved_image
from memoria.imageops.index import handle_new_image
from memoria.imageops.index import handle_replaced_image
from memoria.imageops.sync import fill_image_metadata_from_db
from memoria.models import Image as ImageModel
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageMovedTaskModel
from memoria.tasks.models import ImageReplaceTaskModel
from memoria.utils.hashing import calculate_blake3_hash

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
                image_height=image.original_height,
                image_width=image.original_width,
            )

            updated = fill_image_metadata_from_db(image, metadata)

            if updated:
                metadata_items.append(metadata)

        except Exception:  # noqa: PERF203
            # Log the error with relevant image details
            logger.exception(f"Failed to process metadata for image {image.original_path}")

    if metadata_items:
        with transaction.atomic():
            for item in metadata_items:
                # TODO: Need the path
                write_metadata(Path(), item)
            for image in images:
                image.original_checksum = calculate_blake3_hash(image.original_path, hash_threads=8)
                image.save()
                image.mark_as_clean()


@db_task()
def index_new_images(pkgs: list[ImageIndexTaskModel]) -> None:
    """
    These are all new images (the hash did not already exist), nor did the Path
    """
    with transaction.atomic():
        for pkg in pkgs:
            if not pkg.logger:
                pkg.logger = logger

            pkg.logger.info(f"Indexing {pkg.image_path.name}")

            handle_new_image(pkg)


@db_task()
def index_moved_image(pkgs: list[ImageMovedTaskModel]) -> None:
    """
    Index images with the same checksum, but a new Path
    """
    with transaction.atomic():
        for pkg in pkgs:
            if not pkg.logger:
                pkg.logger = logger

            pkg.logger.info(f"Updating {pkg.image_path.stem}")

            handle_moved_image(pkg)


@db_task()
def index_changed_image(pkgs: list[ImageReplaceTaskModel]) -> None:
    """
    Index images with a new checksum, but an existing Path
    """
    with transaction.atomic():
        for pkg in pkgs:
            if not pkg.logger:
                pkg.logger = logger

            pkg.logger.info(f"Replacing {pkg.image_path.stem} metadata")

            handle_replaced_image(pkg)


@db_task()
def generate_image_files(imgs: list[ImageModel]) -> None:
    """
    TODO: Generate/update thumbnails and large size images.  This is intended for if the site settings change
    or maybe on a new instance?
    """


@db_periodic_task(crontab(minute="0", hour="0"))
@lock_task("trash-delete")
def remove_trashed_images() -> None:
    # Filter images based on deleted_at being less than now - some set period of time and call .delete on the queryset
    # TODO: Set the days from settings
    with transaction.atomic():
        qs = ImageModel.objects.filter(deleted_at__lte=timezone.now() - timedelta(days=30))

        qs.delete()
