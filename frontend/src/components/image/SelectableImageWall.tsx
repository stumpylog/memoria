import React, { useCallback, useEffect, useState } from "react";
import { Button, Col, Container, Row } from "react-bootstrap";

import type { ImageThumbnailSchemaOut } from "../../api";

import SelectableImageCard from "./SelectableImageCard";

interface SelectableImageWallProps {
  images: ImageThumbnailSchemaOut[];
  showViewButton?: boolean;
  onImageClick?: (id: number) => void;
  columns?: number;
  onSelectionChange?: (selectedIds: number[]) => void;
}

const SelectableImageWall: React.FC<SelectableImageWallProps> = ({
  images,
  showViewButton = true,
  onImageClick,
  columns = 3,
  onSelectionChange,
}) => {
  const [selectedImages, setSelectedImages] = useState<number[]>([]);
  const [lastSelectedIndex, setLastSelectedIndex] = useState<number | null>(null);

  // Calculate column width based on the number of columns
  const getColumnClass = () => {
    switch (columns) {
      case 1:
        return "col-12";
      case 2:
        return "col-md-6";
      case 3:
        return "col-md-4";
      case 4:
        return "col-lg-3 col-md-4 col-sm-6";
      case 6:
        return "col-lg-2 col-md-4 col-sm-6";
      default:
        return "col-md-4";
    }
  };

  // Notify parent component when selection changes
  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedImages);
    }
  }, [selectedImages, onSelectionChange]);

  const handleImageSelect = useCallback(
    (imageId: number, event: React.MouseEvent) => {
      const currentIndex = images.findIndex((img) => img.id === imageId);

      // Handle different selection modes
      if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd + Click: Toggle individual selection
        setSelectedImages((prev) => {
          const isSelected = prev.includes(imageId);
          const newSelection = isSelected
            ? prev.filter((id) => id !== imageId)
            : [...prev, imageId];

          setLastSelectedIndex(isSelected ? null : currentIndex);
          return newSelection;
        });
      } else if (event.shiftKey && lastSelectedIndex !== null) {
        // Shift + Click: Select range
        const start = Math.min(lastSelectedIndex, currentIndex);
        const end = Math.max(lastSelectedIndex, currentIndex);

        const rangeIds = images.slice(start, end + 1).map((img) => img.id);

        setSelectedImages((prev) => {
          // Combine previous selection with the new range
          const combined = [...new Set([...prev, ...rangeIds])];
          return combined;
        });

        setLastSelectedIndex(currentIndex);
      } else {
        // Simple click: Clear selection and select only this image
        setSelectedImages([imageId]);
        setLastSelectedIndex(currentIndex);
      }
    },
    [images, lastSelectedIndex],
  );

  const clearSelection = () => {
    setSelectedImages([]);
    setLastSelectedIndex(null);
  };

  return (
    <Container>
      {selectedImages.length > 0 ? (
        <div className="mb-3 d-flex justify-content-between align-items-center">
          <div>
            <span className="me-2">
              {selectedImages.length} image{selectedImages.length !== 1 ? "s" : ""} selected
            </span>
            <Button variant="outline-secondary" size="sm" onClick={clearSelection}>
              Clear Selection
            </Button>
          </div>
        </div>
      ) : null}

      <Row>
        {images.map((image) => (
          <Col key={image.id} className={`${getColumnClass()} mb-4`}>
            <SelectableImageCard
              image={image}
              showViewButton={showViewButton}
              onViewClick={onImageClick}
              isSelected={selectedImages.includes(image.id)}
              onSelect={handleImageSelect}
            />
          </Col>
        ))}
      </Row>
    </Container>
  );
};

export default SelectableImageWall;
