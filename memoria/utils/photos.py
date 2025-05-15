from logging import Logger
from pathlib import Path
from typing import TYPE_CHECKING

import pyvips
from PIL import Image
from PIL import ImageOps


def generate_image_versions_pyvips(
    input_path: Path,
    thumbnail_output_path: Path,
    webp_output_path: Path,
    logger: Logger,
    thumbnail_size: int,
    webp_quality: int,
    scaled_image_side_max: int,
) -> None:
    """
    Creates a thumbnail for an image and saves a potentially scaled-down
    version of the original image as WebP with a specified quality using pyvips.

    The original image is scaled down if its largest side exceeds
    scaled_image_side_max.

    Args:
        input_path: The path to the input image file.
        thumbnail_output_path: The path to save the thumbnail image.
        webp_output_path: The path to save the WebP image.
        logger: The logger instance.
        thumbnail_size: The maximum dimension (width or height) for the thumbnail.
        webp_quality: The quality level for the WebP image (0-100).
        scaled_image_side_max: The maximum dimension (width or height) for the
                                scaled image saved as WebP.
    """
    try:
        # Load the image
        image = pyvips.Image.new_from_file(str(input_path))

        if TYPE_CHECKING:
            assert image is not None
            assert isinstance(image, pyvips.Image)

        # Create and save the thumbnail
        # The thumbnail function resizes the image to fit within the specified size
        logger.info("    Creating thumbnail")
        thumbnail_image = image.thumbnail_image(
            thumbnail_size,
            size=pyvips.enums.Size.BOTH,
            no_rotate=False,
        )
        thumbnail_image.write_to_file(str(thumbnail_output_path))

        image_for_webp = image.autorot()
        original_width = image_for_webp.width
        original_height = image_for_webp.height
        largest_side = max(original_width, original_height)

        if scaled_image_side_max > 0 and largest_side > scaled_image_side_max:
            # Calculate the scaling factor
            scale_factor = scaled_image_side_max / largest_side
            # Resize the image
            image_for_webp = image_for_webp.resize(scale_factor, kernel=pyvips.enums.Kernel.LANCZOS3)

        # Save the image as WebP with specified quality
        # The quality is passed as a keyword argument 'Q'
        logger.info("    Creating WebP version")
        image_for_webp.write_to_file(str(webp_output_path), Q=webp_quality)

    except pyvips.Error:
        logger.exception("An libvips error occurred")
    except FileNotFoundError:
        logger.exception(f"Error: Input file not found at {input_path}")
    except Exception:
        logger.exception("An unexpected error occurred")


def generate_image_versions_pillow(
    input_path: Path,
    thumbnail_output_path: Path,
    webp_output_path: Path,
    logger: Logger,
    thumbnail_size: int,
    webp_quality: int,
    scaled_image_size: int,
) -> None:
    """
    Creates a thumbnail for an image and saves the original image as WebP
    with a specified quality using PIL.

    Args:
        input_path: The path to the input image file.
        thumbnail_output_path: The path to save the thumbnail image.
        webp_output_path: The path to save the WebP image.
        thumbnail_size: The maximum dimension (width or height) for the thumbnail.
        webp_quality: The quality level for the WebP image (0-100).
    """
    with Image.open(input_path) as im_file:
        img_copy = ImageOps.exif_transpose(im_file)
        if TYPE_CHECKING:
            assert img_copy is not None

        logger.info("    Creating thumbnail")
        thumbnail = img_copy.copy()
        thumbnail.thumbnail((thumbnail_size, thumbnail_size))
        thumbnail.save(thumbnail_output_path)

        logger.info("    Creating WebP version")
        # TODO: Make this quality configurable
        img_copy.save(webp_output_path, quality=webp_quality)
