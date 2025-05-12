// src/pages/PeoplePage.tsx
import React from 'react';
import { Container, Card } from 'react-bootstrap';

const PeoplePage: React.FC = () => {
  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">People</Card.Header>
        <Card.Body>
          <Card.Text>This is the people page. Content will be added here.</Card.Text>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default PeoplePage;
