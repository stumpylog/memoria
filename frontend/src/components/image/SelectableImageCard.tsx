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
    e.stopPropagation();
    if (onViewClick) {
      onViewClick(image.id);
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    onSelect(image.id, e);
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
            height={image.thumbnail_height}
            width={image.thumbnail_width}
            style={{
              maxHeight: "100%",
              objectFit: "contain",
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
            }}
          >
            <svg
              className="bi mb-1"
              width="2em"
              height="2em"
              fill="currentColor"
              viewBox="0 0 16 16"
            >
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M5.028 11.02a.5.5 0 0 0-.04.28.99.99 0 0 0 .841.839c.295.054.584.04.84-.028l1.898-2.093a.25.25 0 0 1 .372 0l1.898 2.093c.256.068.545.082.84.028a.99.99 0 0 0 .84-.84.5.5 0 0 0-.04-.28l-1.898-2.092a.25.25 0 0 1 0-.372L10.972 6.98a.5.5 0 0 0 .04-.28.99.99 0 0 0-.841-.839c-.295-.054-.584-.04-.84.028L8.376 8.908a.25.25 0 0 1-.372 0L6.106 6.815c-.256-.068-.545-.082-.84-.028a.99.99 0 0 0-.84.84.5.5 0 0 0 .04.28l1.898 2.092a.25.25 0 0 1 0 .372z" />
            </svg>
            No Thumbnail
            <br />
            Available
          </div>
        )}
        {isSelected && (
          <div
            style={{
              position: "absolute",
              top: "8px",
              right: "8px",
              backgroundColor: "#0d6efd",
              color: "white",
              borderRadius: "50%",
              width: "24px",
              height: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z" />
            </svg>
          </div>
        )}
      </div>
      <Card.Body className="d-flex flex-column">
        <h6 className="card-title">{image.title}</h6>
        {showViewButton && (
          <Button variant="primary" size="sm" className="mt-auto" onClick={handleViewClick}>
            View
          </Button>
        )}
      </Card.Body>
    </Card>
  );
};

export default SelectableImageCard;
