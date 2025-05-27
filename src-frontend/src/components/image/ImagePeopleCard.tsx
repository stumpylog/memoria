// src/components/image/ImagePeopleCard.tsx

import React from "react";
import { Card, ListGroup } from "react-bootstrap";

import type { PersonInImageSchemaOut } from "../../api";

interface ImagePeopleCardProps {
  people: PersonInImageSchemaOut[];
  individualVisibility: Map<number, boolean>; // Individual visibility state
  toggleVisibility: (id: number) => void; // Function to toggle visibility
}

const ImagePeopleCard: React.FC<ImagePeopleCardProps> = ({
  people,
  individualVisibility,
  toggleVisibility,
}) => {
  if (people.length === 0) {
    return null; // Don't render the card if there are no people
  }

  return (
    <Card className="mb-4">
      <Card.Header>
        <h5 className="mb-0">People</h5>
      </Card.Header>
      <ListGroup variant="flush">
        {people.map((personInImage) => {
          // Check if this specific person's box is individually toggled on
          const isIndividuallyVisible = individualVisibility.get(personInImage.id) ?? false;

          return (
            <ListGroup.Item
              key={personInImage.id} // Use actual ID as key
              className={`d-flex justify-content-between align-items-center ${isIndividuallyVisible ? "list-group-item-primary" : ""}`} // Add a class for styling
              onClick={() => toggleVisibility(personInImage.id)}
              style={{ cursor: "pointer" }} // Indicate clickability
            >
              {personInImage.name}
            </ListGroup.Item>
          );
        })}
      </ListGroup>
    </Card>
  );
};

export default ImagePeopleCard;
