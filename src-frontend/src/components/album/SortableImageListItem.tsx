import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import React from "react";
import { Button, Card } from "react-bootstrap";

import type { ImageThumbnailSchemaOut } from "../../api";

interface SortableImageListItemProps {
  image: ImageThumbnailSchemaOut;
  isDragging?: boolean;
  showViewButton?: boolean;
  onViewClick?: (id: number) => void;
}

const SortableImageListItem: React.FC<SortableImageListItemProps> = ({
  image,
  isDragging = false,
  showViewButton = true,
  onViewClick,
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

  const handleViewClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent drag event when button is clicked
    if (onViewClick) {
      onViewClick(image.id);
    }
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners} className="mb-2">
      <Card
        className={`h-100 ${isSortableDragging ? "shadow-lg" : ""}`}
        style={{
          transition: "box-shadow 0.2s ease, opacity 0.2s ease-in-out",
        }}
      >
        <div
          style={{
            height: "200px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            borderBottom: "1px solid rgba(0,0,0,.125)",
            position: "relative",
          }}
        >
          {image.thumbnail_url ? (
            <img
              src={image.thumbnail_url}
              className="card-img-top"
              alt={image.title}
              style={{
                maxHeight: "100%",
                maxWidth: "100%",
                objectFit: "contain",
                pointerEvents: "none",
                height: image.thumbnail_height,
                width: image.thumbnail_width,
              }}
            />
          ) : (
            <div
              style={{
                textAlign: "center",
                color: "#6c757d",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                fontSize: "0.9em",
                height: "100%",
              }}
            >
              <i className="bi bi-image-alt" style={{ fontSize: "2em" }}></i>
              No Thumbnail
            </div>
          )}
        </div>
        <Card.Body className="d-flex flex-column p-2">
          <h6
            className="card-title text-truncate mb-2"
            title={image.title}
            style={{
              fontSize: "0.9rem",
              pointerEvents: "none",
            }}
          >
            {image.title || "Untitled Image"}
          </h6>
          {showViewButton && (
            <Button
              variant="primary"
              size="sm"
              className="mt-auto w-100"
              onClick={handleViewClick}
              style={{ pointerEvents: "auto" }} // Allow button clicks despite drag listeners
            >
              View
            </Button>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default SortableImageListItem;
