/**
 * Transform coordinates based on orientation
 * @param {number} centerX - The center X coordinate (0.0-1.0)
 * @param {number} centerY - The center Y coordinate (0.0-1.0)
 * @param {number} width - The width (0.0-1.0)
 * @param {number} height - The height (0.0-1.0)
 * @param {number} orientation - The orientation (1-8 as per EXIF orientation)
 * @return {Object} - Transformed box with x, y, w, h
 */
function transformCoordinates(centerX, centerY, width, height, orientation) {
  // For MWG regions, these are already center coordinates
  let xPrime, yPrime, wPrime, hPrime;

  // First handle the width/height swap for orientations that need it
  const dimensionsSwapped = [5, 6, 7, 8].includes(orientation);
  wPrime = dimensionsSwapped ? height : width;
  hPrime = dimensionsSwapped ? width : height;

  // Then handle the center point transformations
  switch (orientation) {
    case 1: // Normal
      xPrime = centerX;
      yPrime = centerY;
      break;

    case 2: // Flip horizontal
      xPrime = 1 - centerX;
      yPrime = centerY;
      break;

    case 3: // Rotate 180
      xPrime = 1 - centerX;
      yPrime = 1 - centerY;
      break;

    case 4: // Flip vertical
      xPrime = centerX;
      yPrime = 1 - centerY;
      break;

    case 5: // Transpose (Flip horizontal and rotate 270 CW)
      xPrime = centerY;
      yPrime = centerX;
      break;

    case 6: // Rotate 90 CW
      xPrime = 1 - centerY;
      yPrime = centerX;
      break;

    case 7: // Transverse (Flip horizontal and rotate 90 CW)
      xPrime = 1 - centerY;
      yPrime = 1 - centerX;
      break;

    case 8: // Rotate 270 CW
      xPrime = centerY;
      yPrime = 1 - centerX;
      break;

    default: // Assume normal if orientation is unknown
      xPrime = centerX;
      yPrime = centerY;
      break;
  }

  return {
    x: xPrime,
    y: yPrime,
    w: wPrime,
    h: hPrime,
  };
}
