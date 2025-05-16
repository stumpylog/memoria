from dataclasses import dataclass
from logging import Logger
from pathlib import Path

from PIL import Image
from PIL import ImageOps

Image.MAX_IMAGE_PIXELS = None


@dataclass(slots=True, frozen=True)
class GeneratedFileInfo:
    thumbnail_width: int
    thumbnail_height: int
    large_img_height: int
    large_img_width: int


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
    version of the original image as WebP with a specified quality using Pillow (PIL).
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
    thumbnail_width = thumbnail_height = large_img_height = large_img_width = 0
    try:
        # Use context manager for the initial image load.
        # This ensures the file handle is closed automatically.
        with Image.open(input_path) as img:
            # First, transpose the image according to its EXIF flag
            ImageOps.exif_transpose(img, in_place=True)

            # Create and save the thumbnail
            logger.info("    Creating thumbnail")
            thumb_img = img.copy()
            thumb_img.thumbnail((thumbnail_size, thumbnail_size), Image.Resampling.LANCZOS)
            thumb_img.save(thumbnail_output_path)
            logger.debug(f"Thumbnail saved to {thumbnail_output_path}")
            thumbnail_width, thumbnail_height = thumb_img.size

            # Prepare image for WebP
            # Use another copy derived from the original opened image.
            webp_img = img.copy()

            large_img_width, large_img_height = webp_img.size
            largest_side = max(large_img_height, large_img_width)

            # Check if scaling is needed for the WebP version
            if scaled_image_side_max > 0 and largest_side > scaled_image_side_max:
                logger.debug(
                    f"    Image largest side ({largest_side}) exceeds max ({scaled_image_side_max}), resizing.",
                )
                # Calculate the new dimensions preserving aspect ratio
                if large_img_width > large_img_height:
                    new_width = scaled_image_side_max
                    new_height = int(large_img_height * (scaled_image_side_max / large_img_width))
                else:
                    new_height = scaled_image_side_max
                    new_width = int(large_img_width * (scaled_image_side_max / large_img_height))

                # Resize returns a *new* Image object with the new dimensions
                # Assign the new resized image back to webp_img
                webp_img = webp_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"    Resized image to {new_width}x{new_height}")
            else:
                logger.debug("Image within max size or max size is 0, no scaling needed for WebP.")

            # Save the image as WebP with specified quality
            logger.info("    Creating WebP version")
            # PIL saves the image from the current state of webp_img
            webp_img.save(webp_output_path, format="webp", quality=webp_quality)
            logger.debug(f"WebP image saved to {webp_output_path}")

            return GeneratedFileInfo(thumbnail_width, thumbnail_height, large_img_height, large_img_width)

    except Exception:
        logger.exception("An unexpected error occurred")
        raise
