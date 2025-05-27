import type { ImagesPerPageChoices } from "../api";
/**
 * Given the number of images per page, suggests a suitable number of columns for a grid display.
 * The choice of columns aims for a visually balanced grid, prioritizing common factors.
 *
 * @param imagesPerPage The number of images to display per page (must be one of ImagesPerPageChoices).
 * @returns A suggested number of columns for the grid layout.
 */
export function getGridColumns(imagesPerPage: ImagesPerPageChoices): number {
  switch (imagesPerPage) {
    case 10:
      return 5; // Results in a 5x2 grid
    case 20:
      return 5; // Results in a 5x4 grid
    case 30:
      return 6; // Results in a 6x5 grid
    case 40:
      return 8; // Results in an 8x5 grid
    case 50:
      return 10; // Results in a 10x5 grid
    case 60:
      return 10; // Results in a 10x6 grid
    case 70:
      return 10; // Results in a 10x7 grid
    case 80:
      return 10; // Results in a 10x8 grid
    case 90:
      return 10; // Results in a 10x9 grid
    case 100:
      return 10; // Results in a 10x10 grid (perfect square)
    default:
      // This case should theoretically not be reached due to the type union,
      // but as a safeguard, we could return a default or throw an error.
      // Returning a common default like 5 or 10 is reasonable.
      // For this specific union, 10 is the minimum value in the larger half,
      // and a common factor for many, so returning 10 is a safe fallback.
      return 10;
  }
}
