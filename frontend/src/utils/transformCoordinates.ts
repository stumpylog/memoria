export function transformCoordinates(
  centerX: number,
  centerY: number,
  width: number,
  height: number,
  orientation: number,
) {
  let xPrime, yPrime;
  const dimensionsSwapped = [5, 6, 7, 8].includes(orientation);
  const wPrime = dimensionsSwapped ? height : width;
  const hPrime = dimensionsSwapped ? width : height;

  switch (orientation) {
    case 1:
      xPrime = centerX;
      yPrime = centerY;
      break;
    case 2:
      xPrime = 1 - centerX;
      yPrime = centerY;
      break;
    case 3:
      xPrime = 1 - centerX;
      yPrime = 1 - centerY;
      break;
    case 4:
      xPrime = centerX;
      yPrime = 1 - centerY;
      break;
    case 5:
      xPrime = centerY;
      yPrime = centerX;
      break;
    case 6:
      xPrime = 1 - centerY;
      yPrime = centerX;
      break;
    case 7:
      xPrime = 1 - centerY;
      yPrime = 1 - centerX;
      break;
    case 8:
      xPrime = centerY;
      yPrime = 1 - centerX;
      break;
    default:
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
