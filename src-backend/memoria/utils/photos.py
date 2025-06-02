from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from PIL import Image
from PIL import ImageOps

try:
    import pyvips

    _VIPS_AVAILABLE = True
except ImportError:
    _VIPS_AVAILABLE = False

Image.MAX_IMAGE_PIXELS = None


@dataclass(slots=True, frozen=True)
class GeneratedFileInfo:
    thumbnail_width: int
    thumbnail_height: int
    large_img_height: int
    large_img_width: int


def _calculate_scaled_dimensions(
    original_width: int,
    original_height: int,
    scaled_image_side_max: int,
) -> tuple[int, int]:
    """
    Calculates new dimensions for an image, preserving aspect ratio,
    if its largest side exceeds scaled_image_side_max.
    Returns (new_width, new_height).
    """
    if scaled_image_side_max <= 0:
        return original_width, original_height

    largest_side = max(original_width, original_height)

    if largest_side > scaled_image_side_max:
        if original_width > original_height:
            new_width = scaled_image_side_max
            new_height = int(original_height * (scaled_image_side_max / original_width))
        else:
            new_height = scaled_image_side_max
            new_width = int(original_width * (scaled_image_side_max / original_height))
        return new_width, new_height
    return original_width, original_height


def _generate_with_pillow(
    input_path: Path,
    thumbnail_output_path: Path,
    webp_output_path: Path,
    logger: Logger,
    thumbnail_size: int,
    webp_quality: int,
    scaled_image_side_max: int,
) -> GeneratedFileInfo:
    """
    Generates image versions using Pillow.
    """
    thumbnail_width = thumbnail_height = large_img_height = large_img_width = 0
    with Image.open(input_path) as img:
        # First, transpose the image according to its EXIF flag
        ImageOps.exif_transpose(img, in_place=True)

        # Create and save the thumbnail
        logger.info("    Creating thumbnail with Pillow")
        thumb_img = img.copy()
        thumb_img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
        thumb_img.save(thumbnail_output_path)
        logger.debug(f"Thumbnail saved to {thumbnail_output_path}")
        thumbnail_width, thumbnail_height = thumb_img.size

        # Prepare image for WebP
        webp_img = img.copy()

        large_img_width, large_img_height = webp_img.size

        new_webp_width, new_webp_height = _calculate_scaled_dimensions(
            large_img_width,
            large_img_height,
            scaled_image_side_max,
        )

        if (new_webp_width, new_webp_height) != (large_img_width, large_img_height):
            logger.debug(
                f"    Resizing for WebP from {large_img_width}x{large_img_height} to {new_webp_width}x{new_webp_height}",
            )
            webp_img = webp_img.resize((new_webp_width, new_webp_height), Image.Resampling.LANCZOS)
            large_img_width, large_img_height = new_webp_width, new_webp_height  # Update dimensions after resize
        else:
            logger.debug("Image within max size or max size is 0, no scaling needed for WebP.")

        # Save the image as WebP with specified quality
        logger.info("    Creating WebP version with Pillow")
        webp_img.save(webp_output_path, format="webp", quality=webp_quality)
        logger.debug(f"WebP image saved to {webp_output_path}")

        return GeneratedFileInfo(thumbnail_width, thumbnail_height, large_img_height, large_img_width)


def _generate_with_pyvips(
    input_path: Path,
    thumbnail_output_path: Path,
    webp_output_path: Path,
    logger: Logger,
    thumbnail_size: int,
    webp_quality: int,
    scaled_image_side_max: int,
) -> GeneratedFileInfo:
    """
    Generates image versions using pyvips.
    """
    logger.info("    Using pyvips for image processing.")
    image = pyvips.Image.new_from_file(str(input_path), access="random")

    # Use autorot() to handle EXIF orientation
    image = image.autorot()

    large_img_width, large_img_height = image.width, image.height

    # Create thumbnail
    logger.info("    Creating thumbnail with pyvips")
    # pyvips.thumbnail_image calculates the best crop and resize itself
    thumbnail_image = image.thumbnail_image(
        thumbnail_size,
        size=pyvips.enums.Size.BOTH,
        # Make it also handle the rotation here, just in case
        no_rotate=False,
    )
    thumbnail_image.write_to_file(str(thumbnail_output_path))
    thumbnail_width, thumbnail_height = thumbnail_image.width, thumbnail_image.height

    new_webp_width, new_webp_height = _calculate_scaled_dimensions(
        large_img_width,
        large_img_height,
        scaled_image_side_max,
    )

    if (new_webp_width, new_webp_height) != (large_img_width, large_img_height):
        logger.debug(
            f"    Resizing for WebP from {large_img_width}x{large_img_height} to {new_webp_width}x{new_webp_height}",
        )
        # Calculate scale factor for pyvips.resize()
        scale_factor = (
            (new_webp_width / large_img_width) if large_img_width > 0 else (new_webp_height / large_img_height)
        )
        webp_img = image.resize(scale_factor, kernel="lanczos3")
        large_img_width, large_img_height = webp_img.width, webp_img.height  # Update dimensions after resize
    else:
        logger.debug("Image within max size or max size is 0, no scaling needed for WebP.")

    logger.info("    Creating WebP version with pyvips")
    # For WebP, pyvips uses Q for quality, and can specify lossless=True/False
    webp_img.write_to_file(str(webp_output_path), Q=webp_quality)
    logger.debug(f"WebP image saved to {webp_output_path}")

    return GeneratedFileInfo(thumbnail_width, thumbnail_height, large_img_height, large_img_width)


def generate_image_versions(
    input_path: Path,
    thumbnail_output_path: Path,
    webp_output_path: Path,
    logger: Logger,
    thumbnail_size: int,
    webp_quality: int,
    scaled_image_side_max: int,
) -> GeneratedFileInfo:
    """
    Creates a thumbnail for an image and saves a potentially scaled-down
    version of the original image as WebP with a specified quality.
    Uses pyvips if available, otherwise falls back to Pillow.
    Uses context managers for resource management.

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
        if _VIPS_AVAILABLE:
            return _generate_with_pyvips(
                input_path,
                thumbnail_output_path,
                webp_output_path,
                logger,
                thumbnail_size,
                webp_quality,
                scaled_image_side_max,
            )
        return _generate_with_pillow(
            input_path,
            thumbnail_output_path,
            webp_output_path,
            logger,
            thumbnail_size,
            webp_quality,
            scaled_image_side_max,
        )
    except Exception:
        logger.exception("An unexpected error occurred during image generation")
        raise
