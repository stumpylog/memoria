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

      if (event.ctrlKey || event.metaKey) {
        // Ctrl/Cmd click: Toggle selection of the clicked image
        setSelectedImages((prev) => {
          const isSelected = prev.includes(imageId);
          const newSelection = isSelected
            ? prev.filter((id) => id !== imageId)
            : [...prev, imageId];
          // Update lastSelectedIndex only if adding to selection or if it was the one removed
          if (!isSelected) {
            setLastSelectedIndex(currentIndex);
          } else if (prev.length - 1 === 0) {
            // If last item removed
            setLastSelectedIndex(null);
          } else if (lastSelectedIndex === currentIndex) {
            // If the removed item was the last selected
            // Find the new last selected if possible, or set to null
            // This part can be tricky; for simplicity, could set to null or last item in newSelection
            const lastInNewSelection =
              newSelection.length > 0
                ? images.findIndex((img) => img.id === newSelection[newSelection.length - 1])
                : null;
            setLastSelectedIndex(lastInNewSelection);
          }
          return newSelection;
        });
      } else if (event.shiftKey && lastSelectedIndex !== null && images.length > 0) {
        // Shift click: Select a range
        const start = Math.min(lastSelectedIndex, currentIndex);
        const end = Math.max(lastSelectedIndex, currentIndex);
        const rangeIds = images.slice(start, end + 1).map((img) => img.id);

        // Decide whether to add to current selection or create a new one based on behavior
        // Standard behavior often replaces previous selection part outside the shift-selected range
        // For simplicity here, we add to the existing selection (like Windows Explorer)
        // If you want it to behave like, say, Gmail (replace selection), logic would differ
        setSelectedImages((prev) => {
          // This ensures all items in range are selected, and preserves other selections
          // if that's the desired behavior.
          // For a more "standard" shift-click that might clear other items, you'd filter `prev`
          // or rebuild the selection based on the anchor of the previous non-shift click.
          const combined = [...new Set([...prev, ...rangeIds])];
          return combined;
        });
        // Shift click typically extends from the `lastSelectedIndex` but doesn't change it
        // until a new single click occurs. However, to make subsequent shift-clicks intuitive from
        // the new point, we update it.
        setLastSelectedIndex(currentIndex);
      } else {
        // Single click without modifiers
        if (selectedImages.length === 1 && selectedImages[0] === imageId) {
          // If the clicked image is already the *only* selected image, deselect it.
          setSelectedImages([]);
          setLastSelectedIndex(null);
        } else {
          // Otherwise, select only the clicked image.
          setSelectedImages([imageId]);
          setLastSelectedIndex(currentIndex);
        }
      }
    },
    [images, lastSelectedIndex, selectedImages], // Added selectedImages here
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
