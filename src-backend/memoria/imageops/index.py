from typing import TYPE_CHECKING
from typing import cast

from exifmwg import ExifTool

from memoria.imageops.metadata import update_image_date_from_keywords
from memoria.imageops.metadata import update_image_folder_structure
from memoria.imageops.metadata import update_image_keyword_tree
from memoria.imageops.metadata import update_image_location_from_keywords
from memoria.imageops.metadata import update_image_location_from_mwg
from memoria.imageops.metadata import update_image_people_and_pets
from memoria.models import Image as ImageModel
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageMovedTaskModel
from memoria.tasks.models import ImageReplaceTaskModel
from memoria.utils.hashing import calculate_blake3_hash
from memoria.utils.hashing import calculate_image_phash
from memoria.utils.photos import generate_image_versions

if TYPE_CHECKING:
    from logging import Logger


def handle_moved_image(pkg: ImageMovedTaskModel) -> None:
    """
    Handles an image that has already been indexed, but the location has changed
    """
    pkg.logger = cast("Logger", pkg.logger)

    image = ImageModel.objects.get(pk=pkg.image_id)

    pkg.logger.info("  Image already indexed")
    pkg.logger.info(f"  Updating path from {image.original_path.resolve()} to {pkg.image_path.resolve()}")
    image.original_path = pkg.image_path.resolve()
    image.folder = update_image_folder_structure(pkg)
    image.save()
    image.mark_as_clean()

    if pkg.view_groups:
        if pkg.overwrite:
            image.view_groups.set(pkg.view_groups.all())
        else:
            image.view_groups.add(*pkg.view_groups.all())
    if pkg.edit_groups:
        if pkg.overwrite:
            image.edit_groups.set(pkg.edit_groups.all())
        else:
            image.edit_groups.add(*pkg.edit_groups.all())

    pkg.logger.info(f"  {pkg.image_path.name} updates completed")


def handle_new_image(pkg: ImageIndexTaskModel, tool: ExifTool) -> None:
    """
    Handles a completely new image
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    pkg.logger.info("Processing new image")

    metadata = tool.read_image_metadata(pkg.image_path)

    containing_folder = update_image_folder_structure(pkg)

    new_img: ImageModel = ImageModel.objects.create(
        file_size=pkg.image_path.stat().st_size,
        original=str(pkg.image_path.resolve()),
        title=metadata.Title or pkg.image_path.stem,
        orientation=metadata.Orientation or ImageModel.OrientationChoices.HORIZONTAL,
        description=metadata.Description,
        original_height=metadata.ImageHeight,
        original_width=metadata.ImageWidth,
        original_checksum=pkg.original_hash,
        phash=calculate_image_phash(pkg.image_path),
        folder=containing_folder,
        large_version_height=0,
        large_version_width=0,
        thumbnail_height=0,
        thumbnail_width=0,
        is_dirty=False,
    )

    # Add view/edit permissions
    if pkg.view_groups:
        new_img.view_groups.set(pkg.view_groups.all())
    if pkg.edit_groups:
        new_img.edit_groups.set(pkg.edit_groups.all())

    pkg.logger.info("  Processing image file")

    file_info = generate_image_versions(
        pkg.image_path,
        new_img.thumbnail_path,
        new_img.full_size_path,
        pkg.logger,
        thumbnail_size=pkg.thumbnail_size,
        webp_quality=pkg.large_image_quality,
        scaled_image_side_max=pkg.large_image_size,
    )

    new_img.thumbnail_width = file_info.thumbnail_width
    new_img.thumbnail_height = file_info.thumbnail_height
    new_img.large_version_width = file_info.large_img_width
    new_img.large_version_height = file_info.large_img_height
    new_img.save()

    # Parse Faces/pets/regions
    update_image_people_and_pets(pkg, new_img, metadata)

    # Parse Keywords
    update_image_keyword_tree(pkg, new_img, metadata)

    # Parse Location
    update_image_location_from_mwg(pkg, new_img, metadata)
    if not new_img.location:
        update_image_location_from_keywords(pkg, new_img, metadata)

    # Parse date information from keywords?
    update_image_date_from_keywords(pkg, new_img, metadata)

    # And done.  Image cannot be dirty, use update to avoid getting marked as such
    new_img.mark_as_clean()
    pkg.logger.info("  Indexing completed")


def handle_replaced_image(pkg: ImageReplaceTaskModel, tool: ExifTool) -> None:
    """
    Handles an image that has already been indexed via Path, but the checksum has changed
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    image = ImageModel.objects.get(pk=pkg.image_id)

    if TYPE_CHECKING:
        assert isinstance(image, ImageModel)

    metadata = tool.read_image_metadata(image.original_path)

    image.tags.clear()
    update_image_keyword_tree(pkg, image, metadata)

    image.people.clear()
    image.pets.clear()
    update_image_people_and_pets(pkg, image, metadata)

    image.location = None
    update_image_location_from_mwg(pkg, image, metadata)
    if image.location is None:
        update_image_location_from_keywords(pkg, image, metadata)

    image.folder = update_image_folder_structure(pkg)
    image.date = None
    update_image_date_from_keywords(pkg, image, metadata)

    image.original_checksum = calculate_blake3_hash(image.original_path)
    image.phash = calculate_image_phash(pkg.image_path)

    file_info = generate_image_versions(
        pkg.image_path,
        image.thumbnail_path,
        image.full_size_path,
        pkg.logger,
        thumbnail_size=pkg.thumbnail_size,
        webp_quality=pkg.large_image_quality,
        scaled_image_side_max=pkg.large_image_size,
    )

    image.thumbnail_width = file_info.thumbnail_width
    image.thumbnail_height = file_info.thumbnail_height
    image.large_version_width = file_info.large_img_width
    image.large_version_height = file_info.large_img_height
    image.save()

    image.mark_as_clean()
