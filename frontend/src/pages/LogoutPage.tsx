// src/pages/LogoutPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Container, Card, Button } from 'react-bootstrap';

const LogoutPage: React.FC = () => {
  return (
    <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '80vh' }}>
      <Card style={{ width: '100%', maxWidth: '500px' }} className="text-center">
        <Card.Body>
          <Card.Title>You have been logged out</Card.Title>
          <Card.Text>
            Thank you for using our application. You can log back in at any time.
          </Card.Text>
          <Button as={Link} to="/login" variant="primary">
            Log Back In
          </Button>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default LogoutPage;
