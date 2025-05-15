// src/pages/PeoplePage.tsx

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React from "react";
import { Button, Card, Col, Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { PagedPersonReadOutSchema, PersonReadOutSchema } from "../api";

import { getAllPeople } from "../api";
import { useAuth } from "../hooks/useAuth";

const PeoplePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  // Get pagination parameters from URL or defaults
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10; // Default to 10 if not in profile

  // Calculate offset based on current page and page size
  const offset = (currentPage - 1) * pageSize;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["people", currentPage, pageSize],
    queryFn: async () => {
      const response = await getAllPeople({
        query: {
          limit: pageSize,
          offset: offset,
        },
      });
      return response.data as PagedPersonReadOutSchema;
    },
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000, // Data considered fresh for 5 minutes
  });

  const handleViewDetails = (personId: number) => {
    navigate(`/people/${personId}`);
  };

  const handlePageChange = (page: number) => {
    // Preserve other URL parameters and update only the page
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);

    // Make sure we're at the top of the page when navigating
    window.scrollTo(0, 0);
  };

  // Calculate total pages
  const totalPages = data ? Math.ceil(data.count / pageSize) : 0;

  // Build pagination items
  const paginationItems = [];
  if (totalPages > 0) {
    // Previous button
    paginationItems.push(
      <Button
        key="prev"
        variant="outline-primary"
        className="me-1"
        disabled={currentPage === 1}
        onClick={() => handlePageChange(currentPage - 1)}
      >
        Previous
      </Button>,
    );

    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      paginationItems.push(
        <Button
          key={1}
          variant={currentPage === 1 ? "primary" : "outline-primary"}
          className="me-1"
          onClick={() => handlePageChange(1)}
        >
          1
        </Button>,
      );
      if (startPage > 2) {
        paginationItems.push(
          <span key="ellipsis-start" className="mx-1">
            ...
          </span>,
        );
      }
    }

    for (let page = startPage; page <= endPage; page++) {
      paginationItems.push(
        <Button
          key={page}
          variant={page === currentPage ? "primary" : "outline-primary"}
          className="me-1"
          onClick={() => handlePageChange(page)}
        >
          {page}
        </Button>,
      );
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        paginationItems.push(
          <span key="ellipsis-end" className="mx-1">
            ...
          </span>,
        );
      }
      paginationItems.push(
        <Button
          key={totalPages}
          variant={currentPage === totalPages ? "primary" : "outline-primary"}
          className="me-1"
          onClick={() => handlePageChange(totalPages)}
        >
          {totalPages}
        </Button>,
      );
    }

    // Next button
    paginationItems.push(
      <Button
        key="next"
        variant="outline-primary"
        disabled={currentPage === totalPages}
        onClick={() => handlePageChange(currentPage + 1)}
      >
        Next
      </Button>,
    );
  }

  if (isLoading) {
    return (
      <Container className="mt-4">
        <p>Loading people...</p>
      </Container>
    );
  }

  if (isError) {
    return (
      <Container className="mt-4">
        <p className="text-danger">Error: {(error as Error).message}</p>
      </Container>
    );
  }

  if (!data || data.items.length === 0) {
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
        {data.items.map((person: PersonReadOutSchema) => (
          <Col key={person.id}>
            <Card>
              <Card.Body>
                <Card.Title>{person.name}</Card.Title>
                {person.description && <Card.Text>{person.description}</Card.Text>}
                <Card.Text className="text-muted">Image Count: {person.image_count}</Card.Text>
                <Button variant="primary" onClick={() => handleViewDetails(person.id)}>
                  View Details
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {totalPages > 1 && (
        <div className="d-flex justify-content-center mt-4">
          <div className="d-flex flex-wrap">{paginationItems}</div>
        </div>
      )}

      <div className="mt-3 text-muted">
        Showing {offset + 1}-{Math.min(offset + pageSize, data.count)} of {data.count} people
      </div>
    </Container>
  );
};

export default PeoplePage;
