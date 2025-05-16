// src/components/image/ImagePetsCard.tsx

import React from "react";
import { Card, ListGroup } from "react-bootstrap";

import type { PetInImageSchemaOut } from "../../api";

interface ImagePetsCardProps {
  pets: PetInImageSchemaOut[];
}

const ImagePetsCard: React.FC<ImagePetsCardProps> = ({ pets }) => {
  if (pets.length === 0) {
    return null; // Don't render the card if there are no pets
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <h5 className="mb-0">Pets</h5>
      </Card.Header>
      <ListGroup variant="flush">
        {pets.map((petInImage, index) => (
          <ListGroup.Item
            key={index}
            className="d-flex justify-content-between align-items-center"
          >
            {petInImage.name}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Card>
  );
};

export default ImagePetsCard;
