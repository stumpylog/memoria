import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import React from "react";
import { Card } from "react-bootstrap";

import type { ImageThumbnailSchemaOut } from "../../api";

interface SortableImageListItemProps {
  image: ImageThumbnailSchemaOut;
  isDragging?: boolean;
}

const SortableImageListItem: React.FC<SortableImageListItemProps> = ({
  image,
  isDragging = false,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging: isSortableDragging,
  } = useSortable({ id: image.id.toString() });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging || isSortableDragging ? 0.5 : 1,
    cursor: "grab",
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mb-2">
      <Card
        className={`${isSortableDragging ? "shadow-lg" : ""}`}
        style={{
          transition: "box-shadow 0.2s ease, opacity 0.2s ease-in-out",
        }}
      >
        <Card.Img
          variant="top"
          src={image.thumbnail_url}
          alt={image.title}
          style={{
            height: "150px",
            maxHeight: "100%",
            objectFit: "contain",
            pointerEvents: "none",
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
    </div>
  );
};

export default SortableImageListItem;
