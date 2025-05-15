// src/pages/PeoplePage.tsx

import React, { useEffect, useState } from "react";
import type { PersonReadOutSchema } from "../api";
import { getAllPeople } from "../api";
import { Container, Row, Col, Card, Button } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";

const PeoplePage: React.FC = () => {
  const [people, setPeople] = useState<PersonReadOutSchema[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const navigate = useNavigate(); // Hook for navigation

  useEffect(() => {
    const fetchPeople = async () => {
      setLoading(true);
      setError(null); // Clear previous errors
      try {
        const data = await getAllPeople();
        setPeople(data.data || []);
      } catch (err) {
        console.error("Error fetching people:", err);
        // It's good practice to check if err is an Error instance
        if (err instanceof Error) {
          setError(err);
        } else {
          setError(new Error("An unknown error occurred while fetching people."));
        }
        setPeople(null); // Ensure data is null on error
      } finally {
        setLoading(false);
      }
    };

    fetchPeople();
  }, []); // Empty dependency array means this effect runs only once on mount

  const handleViewDetails = (personId: number) => {
    // Navigate to the details page for the specific person
    navigate(`/people/${personId}`); // Adjust the route path as necessary
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <p>Loading people...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <p className="text-danger">Error: {error.message}</p>
      </Container>
    );
  }

  if (!people || people.length === 0) {
    return (
      <Container className="mt-4">
        <p>No people found.</p>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <Helmet>
        <title>Memoria - People</title>
      </Helmet>
      <h2>People List</h2>
      <Row xs={1} md={2} lg={3} className="g-4">
        {" "}
        {/* Responsive grid */}
        {people.map((person) => (
          <Col key={person.id}>
            <Card>
              {/* Optional: Card.Img top="true" src="..." */}
              <Card.Body>
                <Card.Title>{person.name}</Card.Title>
                {person.description && ( // Conditionally render description
                  <Card.Text>{person.description}</Card.Text>
                )}
                <Card.Text className="text-muted">Image Count: {person.image_count}</Card.Text>
                <Button variant="primary" onClick={() => handleViewDetails(person.id)}>
                  View Details
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    </Container>
  );
};

export default PeoplePage;
