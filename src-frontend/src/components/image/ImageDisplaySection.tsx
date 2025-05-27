// src/components/image/ImageDisplaySection.tsx

import React from "react";
import { Card, Col } from "react-bootstrap";

import type {
  ImageMetadataSchemaOut,
  PersonInImageSchemaOut,
  PetInImageSchemaOut,
} from "../../api";

import { formatBytes } from "../../utils/formatBytes";
import BoundingBoxOverlay from "./BoundingBoxOverlay";

interface ImageDisplaySectionProps {
  metadata: ImageMetadataSchemaOut;
  people: PersonInImageSchemaOut[];
  pets: PetInImageSchemaOut[];
  showPeople: boolean; // Global toggle state
  setShowPeople: React.Dispatch<React.SetStateAction<boolean>>; // Setter for global toggle
  showPets: boolean; // Global toggle state
  setShowPets: React.Dispatch<React.SetStateAction<boolean>>; // Setter for global toggle
  individualPeopleVisibility: Map<number, boolean>; // Individual visibility state
  individualPetsVisibility: Map<number, boolean>; // Individual visibility state
}

const ImageDisplaySection: React.FC<ImageDisplaySectionProps> = ({
  metadata,
  people,
  pets,
  showPeople,
  setShowPeople,
  showPets,
  setShowPets,
  individualPeopleVisibility,
  individualPetsVisibility,
}) => {
  // Filter boxes based on global and individual visibility
  // A box is displayed if it's individually toggled ON OR if the global toggle is ON
  const peopleToDisplay = people.filter(
    (person) => (individualPeopleVisibility.get(person.id) ?? false) || showPeople,
  );

  const petsToDisplay = pets.filter(
    (pet) => (individualPetsVisibility.get(pet.id) ?? false) || showPets,
  );

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
                width={metadata.size.large_version_width}
                height={metadata.size.large_version_height}
                className="img-fluid rounded"
                style={{ maxHeight: "70vh", width: "auto" }}
              />
              {/* Render BoundingBoxOverlay only if there are people to display */}
              {peopleToDisplay.length > 0 && (
                <BoundingBoxOverlay
                  boxes={peopleToDisplay} // Pass filtered list
                  orientation={metadata.orientation || 1}
                  color="rgba(0, 123, 255, 0.5)" // Blue with opacity
                  labelKey="name"
                />
              )}
              {/* Render BoundingBoxOverlay only if there are pets to display */}
              {petsToDisplay.length > 0 && (
                <BoundingBoxOverlay
                  boxes={petsToDisplay} // Pass filtered list
                  orientation={metadata.orientation || 1}
                  color="rgba(255, 193, 7, 0.5)" // Amber/Yellow with opacity
                  labelKey="name"
                />
              )}
            </div>
          </Card.Body>
          <Card.Footer className="d-flex justify-content-between flex-wrap">
            {/* ... existing dimension and size display ... */}
            <span>
              {metadata.size.original_width}x{metadata.size.original_height} px
            </span>
            <span>{metadata.file_size ? formatBytes(metadata.file_size) : "Unknown size"}</span>
            <div className="d-flex">
              {/* Toggle for People bounding boxes (Global) */}
              <div className="form-check form-switch ms-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="personBoundingBoxToggle"
                  disabled={people.length === 0} // Disable if no people exist
                  checked={showPeople}
                  onChange={() => setShowPeople(!showPeople)}
                />
                <label className="form-check-label" htmlFor="personBoundingBoxToggle">
                  Show All People
                </label>
              </div>
              {/* Toggle for Pets bounding boxes (Global) */}
              <div className="form-check form-switch ms-3">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="petBoundingBoxToggle"
                  disabled={pets.length === 0} // Disable if no pets exist
                  checked={showPets}
                  onChange={() => setShowPets(!showPets)}
                />
                <label className="form-check-label" htmlFor="petBoundingBoxToggle">
                  Show All Pets
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
