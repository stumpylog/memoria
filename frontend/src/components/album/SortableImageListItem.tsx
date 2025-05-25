import React from "react";
import { Card } from "react-bootstrap";

import type { ImageThumbnailSchemaOut } from "../../api"; //

interface SortableImageListItemProps {
  image: ImageThumbnailSchemaOut;
  onDragStart: (event: React.DragEvent<HTMLDivElement>, imageId: number) => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>, targetImageId: number) => void;
  onDragEnd: (event: React.DragEvent<HTMLDivElement>) => void;
  isDragging?: boolean; // Optional: for styling the dragged item
}

const SortableImageListItem: React.FC<SortableImageListItemProps> = ({
  image,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  isDragging,
}) => {
  return (
    <Card
      draggable
      onDragStart={(e) => onDragStart(e, image.id)}
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, image.id)}
      onDragEnd={onDragEnd}
      className="mb-2"
      style={{
        cursor: "grab",
        opacity: isDragging ? 0.5 : 1,
        transition: "opacity 0.2s ease-in-out",
      }}
    >
      <Card.Img
        variant="top"
        src={image.thumbnail_url}
        alt={image.title}
        style={{
          height: "150px",
          objectFit: "contain",
          pointerEvents: "none", // Prevents image's default drag behavior
        }}
      />
      <Card.Body className="p-2">
        <Card.Text
          className="text-truncate small"
          title={image.title}
          style={{ pointerEvents: "none" }}
        >
          {image.title || "Untitled"}
        </Card.Text>
      </Card.Body>
    </Card>
  );
};

export default SortableImageListItem;
