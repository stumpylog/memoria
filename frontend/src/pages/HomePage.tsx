// src/pages/HomePage.tsx
import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { Container, Row, Col, Card } from 'react-bootstrap';

const HomePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <Container fluid className="p-4">
      <Row className="justify-content-md-center">
        <Col md={8}>
          <Card>
            <Card.Header as="h2">Welcome!</Card.Header>
            <Card.Body>
              {user ? (
                <Card.Text>
                  Hello, <strong>{user.first_name || user.username}</strong>! Welcome to the application.
                </Card.Text>
              ) : (
                <Card.Text>Loading user information...</Card.Text>
              )}
              <Card.Text>
                This is your dashboard. Navigate using the links above.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default HomePage;
