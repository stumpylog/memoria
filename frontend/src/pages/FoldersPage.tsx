// src/pages/FoldersPage.tsx
import React from 'react';
import { Container, Card } from 'react-bootstrap';

const FoldersPage: React.FC = () => {
  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">Folders</Card.Header>
        <Card.Body>
          <Card.Text>This is the folders page. Content will be added here.</Card.Text>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default FoldersPage;
