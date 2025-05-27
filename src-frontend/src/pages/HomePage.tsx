import React from "react";
import { Card, Col, Container, Row } from "react-bootstrap";

import StatisticsDisplay from "../components/StatisticsComponent"; // Assuming this is the correct path
import { useAuth } from "../hooks/useAuth";

const HomePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <Container fluid className="p-4">
      <Row className="justify-content-center align-items-start">
        {" "}
        {/* Center the content row and align items to the top */}
        <Col md={8} className="mb-4 mb-md-0">
          {" "}
          {/* Main card takes 8 columns on medium screens and up */}
          <Card>
            <Card.Header as="h2">Welcome!</Card.Header>
            <Card.Body>
              {user ? (
                <Card.Text>
                  Hello, <strong>{user.first_name || user.username}</strong>! Welcome to the
                  application.
                </Card.Text>
              ) : (
                <Card.Text>Loading user information...</Card.Text>
              )}
              <Card.Text>This is your dashboard. Navigate using the links above.</Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          {" "}
          {/* Statistics display now takes 4 columns on medium screens and up */}
          <StatisticsDisplay />
        </Col>
      </Row>
    </Container>
  );
};

export default HomePage;
