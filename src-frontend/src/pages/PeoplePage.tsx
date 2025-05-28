// src/pages/PeoplePage.tsx

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  Container,
  FormControl,
  InputGroup,
  OverlayTrigger, // Import OverlayTrigger
  Pagination,
  Table,
  Tooltip, // Import Tooltip
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { PagedPersonReadOutSchema, PersonReadOutSchema } from "../api";

import { getAllPeople } from "../api";
import { useAuth } from "../hooks/useAuth";

const PeoplePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  // State for search term
  const [searchTerm, setSearchTerm] = useState(searchParams.get("person_name") || "");
  // Ref for the search input to manage debounce
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Get pagination parameters from URL or defaults
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10; // Default to 10 if not in profile

  // Calculate offset based on current page and page size
  const offset = (currentPage - 1) * pageSize;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["people", currentPage, pageSize, searchTerm],
    queryFn: async ({ signal }) => {
      const response = await getAllPeople({
        query: {
          limit: pageSize,
          offset: offset,
          person_name: searchTerm || undefined, // Only send if not empty
        },
        signal, // Pass the AbortController signal to the fetch request
      });
      return response.data as PagedPersonReadOutSchema;
    },
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000, // Data considered fresh for 5 minutes
  });

  // Debounce effect for search term
  useEffect(() => {
    const handler = setTimeout(() => {
      const newParams = new URLSearchParams(searchParams);
      if (searchTerm) {
        newParams.set("person_name", searchTerm);
      } else {
        newParams.delete("person_name");
      }
      // Reset to first page when search term changes
      newParams.set("page", "1");
      setSearchParams(newParams);
    }, 500); // 500ms debounce

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, searchParams, setSearchParams]);

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

  const renderPaginationItems = () => {
    const items = [];
    if (totalPages === 0) return null;

    items.push(
      <Pagination.Prev
        key="prev"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
      />,
    );

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      items.push(
        <Pagination.Item key={1} active={currentPage === 1} onClick={() => handlePageChange(1)}>
          1
        </Pagination.Item>,
      );
      if (startPage > 2) {
        items.push(<Pagination.Ellipsis key="ellipsis-start" />);
      }
    }

    for (let page = startPage; page <= endPage; page++) {
      items.push(
        <Pagination.Item
          key={page}
          active={page === currentPage}
          onClick={() => handlePageChange(page)}
        >
          {page}
        </Pagination.Item>,
      );
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        items.push(<Pagination.Ellipsis key="ellipsis-end" />);
      }
      items.push(
        <Pagination.Item
          key={totalPages}
          active={currentPage === totalPages}
          onClick={() => handlePageChange(totalPages)}
        >
          {totalPages}
        </Pagination.Item>,
      );
    }

    items.push(
      <Pagination.Next
        key="next"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      />,
    );
    return <Pagination>{items}</Pagination>;
  };

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

  // Function to truncate description
  const truncateDescription = (text: string | undefined, maxLength: number) => {
    if (!text) return "N/A";
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  return (
    <Container className="mt-4">
      <title>Memoria - People</title>
      <h2 className="mb-4">People List</h2>

      <InputGroup className="mb-3">
        <FormControl
          placeholder="Search by person name..."
          aria-label="Search by person name"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          ref={searchInputRef}
        />
        <Button variant="outline-secondary" disabled>
          <i className="bi bi-search"></i>
        </Button>
      </InputGroup>

      {(!data || data.items.length === 0) && <p>No people found matching your criteria.</p>}

      {data && data.items.length > 0 && (
        <>
          <Table striped bordered hover responsive className="mt-3">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Image Count</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((person: PersonReadOutSchema) => (
                <tr key={person.id}>
                  <td>{person.name}</td>
                  <td>
                    {person.description && person.description.length > 50 ? (
                      <OverlayTrigger
                        placement="top"
                        delay={{ show: 250, hide: 400 }}
                        overlay={
                          <Tooltip id={`tooltip-${person.id}`}>{person.description}</Tooltip>
                        }
                      >
                        <span>{truncateDescription(person.description, 50)}</span>
                      </OverlayTrigger>
                    ) : (
                      person.description || "N/A"
                    )}
                  </td>
                  <td>{person.image_count}</td>
                  <td>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => handleViewDetails(person.id)}
                    >
                      View Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {totalPages > 1 && (
            <div className="d-flex justify-content-center mt-4">{renderPaginationItems()}</div>
          )}

          <div className="mt-3 text-muted">
            Showing {offset + 1}-{Math.min(offset + pageSize, data.count)} of {data.count} people
          </div>
        </>
      )}
    </Container>
  );
};

export default PeoplePage;
