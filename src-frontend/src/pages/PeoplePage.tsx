// src/pages/PeoplePage.tsx

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  Container,
  FormControl,
  InputGroup,
  OverlayTrigger,
  Pagination,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { PagedPersonReadOutSchema, PersonReadOutSchema } from "../api";

import { getAllPeople } from "../api";
import { useAuth } from "../hooks/useAuth";

// Define a type alias for the allowed sort_by values, matching your backend Literal
type SortByValue = "name" | "-name" | "image_count" | "-image_count";

const PeoplePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  // State for search term
  const [searchTerm, setSearchTerm] = useState(searchParams.get("person_name") || "");
  // Ref for the search input to manage debounce
  const searchInputRef = useRef<HTMLInputElement>(null);

  // State for sorting: Stores the raw sort_by string (e.g., "name", "-name", "image_count", "-image_count")
  // The default sort when nothing is specified or cleared is "name" (ascending).
  // Explicitly type the useState to SortByValue
  const [sortBy, setSortBy] = useState<SortByValue>(() => {
    const param = searchParams.get("sort_by");
    // Validate the param against the allowed literal values
    if (
      param === "name" ||
      param === "-name" ||
      param === "image_count" ||
      param === "-image_count"
    ) {
      return param;
    }
    return "name"; // Default to "name" (ascending) if the param is invalid or not present
  });

  // Get pagination parameters from URL or defaults
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10; // Default to 10 if not in profile

  // Calculate offset based on current page and page size
  const offset = (currentPage - 1) * pageSize;

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["people", currentPage, pageSize, searchTerm, sortBy], // Add sortBy to queryKey
    queryFn: async ({ signal }) => {
      const response = await getAllPeople({
        query: {
          limit: pageSize,
          offset: offset,
          person_name: searchTerm || undefined,
          sort_by: sortBy, // Pass the sortBy state directly to the API
        },
        signal,
      });
      return response.data as PagedPersonReadOutSchema;
    },
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
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
    }, 500);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, searchParams, setSearchParams]);

  // Effect for sortBy changes
  useEffect(() => {
    const newParams = new URLSearchParams(searchParams);
    // Only set sort_by if it's not the default "name", otherwise delete it for cleaner URLs
    if (sortBy && sortBy !== "name") {
      newParams.set("sort_by", sortBy);
    } else {
      newParams.delete("sort_by");
    }
    // Reset to first page when sort column or direction changes
    newParams.set("page", "1");
    setSearchParams(newParams);
  }, [sortBy, searchParams, setSearchParams]);

  const handleViewDetails = (personId: number) => {
    navigate(`/people/${personId}`);
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    window.scrollTo(0, 0);
  };

  // Function to handle sorting when a table header is clicked
  const handleSortChange = (column: "name" | "image_count") => {
    let newSortBy: SortByValue; // Explicitly type newSortBy here

    if (sortBy === column) {
      // Currently ascending for this column -> switch to descending
      newSortBy = `-${column}`;
    } else if (sortBy === `-${column}`) {
      // Currently descending for this column -> clear sort (go back to default 'name' ascending)
      newSortBy = "name";
    } else {
      // Sorting by another column or no sort -> sort by this column ascending
      newSortBy = column;
    }
    setSortBy(newSortBy);
  };

  // Helper function to get the current sort icon
  const getSortIcon = (column: "name" | "image_count") => {
    if (sortBy === column) {
      return <i className="bi bi-caret-up-fill ms-1"></i>; // Ascending icon
    } else if (sortBy === `-${column}`) {
      return <i className="bi bi-caret-down-fill ms-1"></i>; // Descending icon
    }
    return null; // No icon if not sorted by this column
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
                <th onClick={() => handleSortChange("name")} style={{ cursor: "pointer" }}>
                  Name {getSortIcon("name")}
                </th>
                <th>Description</th>
                <th onClick={() => handleSortChange("image_count")} style={{ cursor: "pointer" }}>
                  Image Count {getSortIcon("image_count")}
                </th>
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
