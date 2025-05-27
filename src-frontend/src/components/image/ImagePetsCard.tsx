// src/components/image/ImagePetsCard.tsx

import React from "react";
import { Card, ListGroup } from "react-bootstrap";

import type { PetInImageSchemaOut } from "../../api";

interface ImagePetsCardProps {
  pets: PetInImageSchemaOut[];
  individualVisibility: Map<number, boolean>; // Individual visibility state
  toggleVisibility: (id: number) => void; // Function to toggle visibility
}

const ImagePetsCard: React.FC<ImagePetsCardProps> = ({
  pets,
  individualVisibility,
  toggleVisibility,
}) => {
  if (pets.length === 0) {
    return null; // Don't render the card if there are no pets
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <h5 className="mb-0">Pets</h5>
      </Card.Header>
      <ListGroup variant="flush">
        {pets.map((petInImage) => {
          // Check if this specific pet's box is individually toggled on
          const isIndividuallyVisible = individualVisibility.get(petInImage.id) ?? false;

          return (
            <ListGroup.Item
              key={petInImage.id} // Use actual ID as key
              className={`d-flex justify-content-between align-items-center ${isIndividuallyVisible ? "list-group-item-warning" : ""}`} // Add a class for styling
              onClick={() => toggleVisibility(petInImage.id)}
              style={{ cursor: "pointer" }} // Indicate clickability
            >
              {petInImage.name}
            </ListGroup.Item>
          );
        })}
      </ListGroup>
    </Card>
  );
};

export default ImagePetsCard;
