// src/components/image/BoundingBoxOverlay.tsx

import React from "react";

import { transformCoordinates } from "../../utils/transformCoordinates";

interface Box {
  id: number; // Assuming boxes have an ID for tracking
  center_x: number;
  center_y: number;
  width: number;
  height: number;
  [key: string]: any; // Allow other properties like 'name'
}

interface Props {
  boxes: Box[];
  orientation: number;
  color: string;
  labelKey: string;
}

const BoundingBoxOverlay: React.FC<Props> = ({ boxes, orientation, color, labelKey }) => {
  return (
    <>
      {boxes.map((box) => {
        // Transform coordinates based on orientation
        const { x, y, w, h } = transformCoordinates(
          box.center_x,
          box.center_y,
          box.width,
          box.height,
          orientation,
        );

        // Calculate CSS styles for absolute positioning
        const left = `${(x - w / 2) * 100}%`;
        const top = `${(y - h / 2) * 100}%`;
        const width = `${w * 100}%`;
        const height = `${h * 100}%`;

        return (
          <div
            key={box.id} // Use box ID as key
            className="bounding-box"
            style={{
              position: "absolute",
              left,
              top,
              width,
              height,
              border: `2px solid ${color}`,
              backgroundColor: color,
              opacity: 0.25, // Keep consistent opacity for displayed boxes
            }}
            title={box[labelKey]} // Display label on hover
          />
        );
      })}
    </>
  );
};

export default BoundingBoxOverlay;
