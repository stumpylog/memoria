// src/components/image/ImagePeopleCard.tsx

import React from "react";
import { Card, ListGroup } from "react-bootstrap";

import type { PersonInImageSchemaOut } from "../../api";

interface ImagePeopleCardProps {
  people: PersonInImageSchemaOut[];
}

const ImagePeopleCard: React.FC<ImagePeopleCardProps> = ({ people }) => {
  if (people.length === 0) {
    return null; // Don't render the card if there are no people
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <h5 className="mb-0">People</h5>
      </Card.Header>
      <ListGroup variant="flush">
        {people.map((personInImage, index) => (
          <ListGroup.Item
            key={index}
            className="d-flex justify-content-between align-items-center"
          >
            {personInImage.name}
          </ListGroup.Item>
        ))}
      </ListGroup>
    </Card>
  );
};

export default ImagePeopleCard;
