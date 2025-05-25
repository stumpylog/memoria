import React from "react";
import { Button, Card } from "react-bootstrap";

import type { ImageThumbnailSchemaOut } from "../../api";

interface SelectableImageCardProps {
  image: ImageThumbnailSchemaOut;
  showViewButton?: boolean;
  onViewClick?: (id: number) => void;
  isSelected: boolean;
  onSelect: (id: number, event: React.MouseEvent) => void;
}

const SelectableImageCard: React.FC<SelectableImageCardProps> = ({
  image,
  showViewButton = true,
  onViewClick,
  isSelected,
  onSelect,
}) => {
  const handleViewClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click event when button is clicked
    if (onViewClick) {
      onViewClick(image.id);
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // Allow selecting only if the click is not on the view button
    if (
      !(e.target instanceof HTMLElement && e.target.closest("button")) &&
      !(e.target instanceof SVGElement && e.target.closest("button")) // handle clicks on svg inside button
    ) {
      onSelect(image.id, e);
    }
  };

  const selectionIndicatorStyle: React.CSSProperties = {
    position: "absolute",
    top: "8px",
    right: "8px",
    width: "24px",
    height: "24px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "background-color 0.2s ease-in-out, border-color 0.2s ease-in-out",
    border: `2px solid ${isSelected ? "#0d6efd" : "#adb5bd"}`, // Use theme primary or a neutral border
    backgroundColor: isSelected ? "#0d6efd" : "rgba(255, 255, 255, 0.7)", // Semi-transparent white for unselected
    color: isSelected ? "white" : "transparent", // Checkmark color
    zIndex: 10, // Ensure it's above the image
  };

  return (
    <Card
      className={`h-100 ${isSelected ? "border-primary" : ""}`}
      onClick={handleCardClick}
      style={{
        cursor: "pointer",
        boxShadow: isSelected ? "0 0 0 2px #0d6efd" : "none",
        transition: "all 0.2s ease-in-out",
      }}
    >
      <div
        style={{
          height: "200px", // Or your preferred image container height
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          borderBottom: "1px solid rgba(0,0,0,.125)",
          position: "relative", // For positioning the selection indicator
        }}
      >
        {image.thumbnail_url ? (
          <img
            src={image.thumbnail_url}
            className="card-img-top" // Ensures responsiveness within the div
            alt={image.title}
            style={{
              maxHeight: "100%",
              maxWidth: "100%", // Ensure image does not overflow its container
              objectFit: "contain", // Was 'contain', ensures whole image is visible
              height: image.thumbnail_height, // Set explicit height/width if available
              width: image.thumbnail_width, // and if it makes sense for your layout
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
              height: "100%", // Ensure placeholder takes full height
            }}
          >
            <i className="bi bi-image-alt" style={{ fontSize: "2em" }}></i>
            No Thumbnail
          </div>
        )}

        {/* Selection Indicator Circle */}
        <div style={selectionIndicatorStyle}>
          {isSelected && (
            <svg
              width="14" // Slightly smaller to fit well within the 24px circle
              height="14"
              fill="currentColor"
              viewBox="0 0 16 16"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
            </svg>
          )}
        </div>
      </div>
      <Card.Body className="d-flex flex-column p-2">
        {" "}
        {/* Reduced padding for smaller cards */}
        <h6
          className="card-title text-truncate mb-2"
          title={image.title}
          style={{ fontSize: "0.9rem" }}
        >
          {image.title || "Untitled Image"}
        </h6>
        {showViewButton && (
          <Button
            variant="primary"
            size="sm"
            className="mt-auto w-100" // Make button take full width of its container
            onClick={handleViewClick}
          >
            View
          </Button>
        )}
      </Card.Body>
    </Card>
  );
};

export default SelectableImageCard;
