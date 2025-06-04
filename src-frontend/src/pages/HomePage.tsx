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
              <Card.Text>
                This is your dashboard. Navigate using the links above.
                <br />
                <br />
                <strong>Folders</strong> show the folders scans were stored in when they were
                index. Browse them like a file system.
                <br />
                <strong>People & Pets</strong> allows you to browse images which contain a named
                person or pet.
                <br />
                <strong>Albums</strong> can be created and shared by you. Pictures inside albums
                can be sorted however you want by drag and drop.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <StatisticsDisplay />
        </Col>
      </Row>
    </Container>
  );
};

export default HomePage;
