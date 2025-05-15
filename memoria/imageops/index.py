from typing import TYPE_CHECKING
from typing import cast

from exifmwg import ExifTool
from PIL import Image

from memoria.imageops.metadata import update_image_date_from_keywords
from memoria.imageops.metadata import update_image_folder_structure
from memoria.imageops.metadata import update_image_keyword_tree
from memoria.imageops.metadata import update_image_location_from_keywords
from memoria.imageops.metadata import update_image_location_from_mwg
from memoria.imageops.metadata import update_image_people_and_pets
from memoria.models import Image as ImageModel
from memoria.tasks.models import ImageIndexTaskModel
from memoria.tasks.models import ImageUpdateTaskModel
from memoria.utils.hashing import calculate_image_phash
from memoria.utils.photos import generate_image_versions_pyvips

if TYPE_CHECKING:
    from logging import Logger

# We will just trust the images
Image.MAX_IMAGE_PIXELS = None


def handle_existing_image(pkg: ImageUpdateTaskModel) -> None:
    """
    Handles an image that has already been indexed, either updating its source or changing the location
    """
    pkg.logger = cast("Logger", pkg.logger)

    pkg.logger.info("  Image already indexed")
    # Set the source if requested
    # Check for an updated location
    if pkg.image_path.resolve() != pkg.image.original_path.resolve():
        pkg.logger.info(f"  Updating path from {pkg.image.original_path.resolve()} to {pkg.image_path.resolve()}")
        pkg.image.original_path = pkg.image_path.resolve()
        pkg.image.save()
        pkg.image.mark_as_clean()
    else:
        pkg.logger.debug("  Original path is still matching")

    if pkg.view_groups:
        if pkg.overwrite:
            pkg.image.view_groups.set(pkg.view_groups.all())
        else:
            pkg.image.view_groups.add(*pkg.view_groups.all())
    if pkg.edit_groups:
        if pkg.overwrite:
            pkg.image.edit_groups.set(pkg.edit_groups.all())
        else:
            pkg.image.edit_groups.add(*pkg.edit_groups.all())

    pkg.logger.info(f"  {pkg.image_path.name} indexing completed")


def handle_new_image(pkg: ImageIndexTaskModel, tool: ExifTool) -> None:
    """
    Handles a completely new image
    """

    if TYPE_CHECKING:
        assert pkg.logger is not None

    pkg.logger.info("Processing new image")

    metadata = tool.read_image_metadata(pkg.image_path)

    containing_folder = update_image_folder_structure(pkg)

    new_img = ImageModel.objects.create(
        file_size=pkg.image_path.stat().st_size,
        original=str(pkg.image_path.resolve()),
        title=metadata.Title or pkg.image_path.stem,
        orientation=metadata.Orientation or ImageModel.OrientationChoices.HORIZONTAL,
        description=metadata.Description,
        original_height=metadata.ImageHeight,
        original_width=metadata.ImageWidth,
        original_checksum=pkg.original_hash,
        phash=calculate_image_phash(pkg.image_path),
        # Relations
        folder=containing_folder,
        # These are placeholders, the files do not exist yet
        # thumbnail_checksum="A",
        # full_size_checksum="B",
        thumbnail_height=0,
        thumbnail_width=0,
        # This time cannot be dirty
        is_dirty=False,
    )

    # Add view/edit permissions
    if pkg.view_groups:
        new_img.view_groups.set(pkg.view_groups.all())
    if pkg.edit_groups:
        new_img.edit_groups.set(pkg.edit_groups.all())

    pkg.logger.info("  Processing image file")

    generate_image_versions_pyvips(
        pkg.image_path,
        new_img.thumbnail_path,
        new_img.full_size_path,
        pkg.logger,
        thumbnail_size=pkg.thumbnail_size,
        webp_quality=pkg.large_image_quality,
        scaled_image_side_max=pkg.large_image_size,
    )

    # Update the file hashes, now that the files exist
    # pkg.logger.info("    Hashing created files")
    # new_img.thumbnail_checksum = calculate_blake3_hash(new_img.thumbnail_path, hash_threads=pkg.hash_threads)
    # new_img.full_size_checksum = calculate_blake3_hash(new_img.full_size_path, hash_threads=pkg.hash_threads)
    with Image.open(new_img.thumbnail_path) as img:
        new_img.thumbnail_width, new_img.thumbnail_height = img.size
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
