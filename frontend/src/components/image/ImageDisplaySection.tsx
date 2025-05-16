// src/components/image/ImageDisplaySection.tsx

import React from "react";
import { Card, Col } from "react-bootstrap";

import type { ImageMetadataSchema, PersonInImageSchemaOut, PetInImageSchemaOut } from "../../api";

import { formatBytes } from "../../utils/formatBytes";
import BoundingBoxOverlay from "./BoundingBoxOverlay";

interface ImageDisplaySectionProps {
  metadata: ImageMetadataSchema;
  people: PersonInImageSchemaOut[];
  pets: PetInImageSchemaOut[];
  showPeople: boolean;
  setShowPeople: React.Dispatch<React.SetStateAction<boolean>>;
  showPets: boolean;
  setShowPets: React.Dispatch<React.SetStateAction<boolean>>;
}

const ImageDisplaySection: React.FC<ImageDisplaySectionProps> = ({
  metadata,
  people,
  pets,
  showPeople,
  setShowPeople,
  showPets,
  setShowPets,
}) => {
  return (
    <Col md={8}>
      {metadata.larger_size_url ? (
        <Card>
          <Card.Body className="p-1 text-center">
            <div
              id="imageContainer"
              style={{ position: "relative", display: "inline-block" }}
              data-orientation={metadata.orientation}
            >
              <img
                id="mainImage"
                src={metadata.larger_size_url}
                alt={metadata.title || "Image"}
                className="img-fluid rounded"
                style={{ maxHeight: "70vh", width: "auto" }}
              />
              {showPeople && people && people.length > 0 && (
                <BoundingBoxOverlay
                  boxes={people}
                  orientation={metadata.orientation || 1}
                  color="rgba(0, 123, 255, 0.5)" // Blue with opacity
                  labelKey="name"
                />
              )}
              {showPets && pets && pets.length > 0 && (
                <BoundingBoxOverlay
                  boxes={pets}
                  orientation={metadata.orientation || 1}
                  color="rgba(255, 193, 7, 0.5)" // Amber/Yellow with opacity
                  labelKey="name"
                />
              )}
            </div>
          </Card.Body>
          <Card.Footer className="d-flex justify-content-between flex-wrap">
            <span>
              {metadata.original_width}x{metadata.original_height} px
            </span>
            <span>{metadata.file_size ? formatBytes(metadata.file_size) : "Unknown size"}</span>
            <div className="d-flex">
              {/* Toggle for People bounding boxes */}
              <div className="form-check form-switch ms-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="personBoundingBoxToggle"
                  disabled={people.length === 0}
                  checked={showPeople}
                  onChange={() => setShowPeople(!showPeople)}
                />
                <label className="form-check-label" htmlFor="personBoundingBoxToggle">
                  Show People
                </label>
              </div>
              {/* Toggle for Pets bounding boxes */}
              <div className="form-check form-switch ms-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="petBoundingBoxToggle"
                  disabled={pets.length === 0}
                  checked={showPets}
                  onChange={() => setShowPets(!showPets)}
                />
                <label className="form-check-label" htmlFor="petBoundingBoxToggle">
                  Show Pets
                </label>
              </div>
            </div>
          </Card.Footer>
        </Card>
      ) : (
        <div className="alert alert-warning" role="alert">
          Full image not available.
        </div>
      )}
    </Col>
  );
};

export default ImageDisplaySection;
