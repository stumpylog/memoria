// src/pages/PeoplePage.tsx

import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  Container,
  FormControl,
  InputGroup,
  OverlayTrigger,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { PagedPersonReadOutSchema, PersonReadOutSchema } from "../api";

import { getAllPeople } from "../api";
import PaginationComponent from "../components/common/PaginationComponent";
import { useAuth } from "../hooks/useAuth";
import { truncateString } from "../utils/truncateString";

// Define a type alias for the allowed sort_by values, matching your backend Literal
type SortByValue = "name" | "-name" | "image_count" | "-image_count";

const PeoplePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();
  const queryClient = useQueryClient();

  // State for search term
  const [searchTerm, setSearchTerm] = useState(searchParams.get("person_name") || "");
  // Ref for the search input to manage debounce
  const searchInputRef = useRef<HTMLInputElement>(null);
  const prevSearchTermRef = useRef(searchTerm);

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
  const prevSortByRef = useRef(sortBy);

  // Get pagination parameters from URL or defaults
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10; // Default to 10 if not in profile
  // Calculate offset based on current page and page size
  const offset = (currentPage - 1) * pageSize;

  const currentQueryKeyPage = searchParams.get("page") || "1";

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: ["people", currentQueryKeyPage, pageSize, searchTerm, sortBy],
    queryFn: async ({ signal }) => {
      const response = await getAllPeople({
        query: {
          limit: pageSize,
          offset: offset,
          person_name: searchTerm || undefined,
          sort_by: sortBy,
        },
        signal,
      });
      return response.data as PagedPersonReadOutSchema;
    },
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });

  // Effect for search term changes, only runs when searchTerm state itself changes significantly
  useEffect(() => {
    // Only update searchParams if searchTerm has genuinely changed
    // This effect should handle updating the URL when searchTerm changes
    if (searchTerm !== prevSearchTermRef.current) {
      const newParams = new URLSearchParams(searchParams);
      if (searchTerm) {
        newParams.set("person_name", searchTerm);
      } else {
        newParams.delete("person_name");
      }
      newParams.set("page", "1"); // Always reset to page 1 on search term change
      setSearchParams(newParams);
      prevSearchTermRef.current = searchTerm; // Update the ref
    }
  }, [searchTerm, searchParams, setSearchParams]); // Keep searchParams in dependencies for the latest version

  // Effect for sortBy changes, only runs when sortBy state itself changes significantly
  useEffect(() => {
    // Only update searchParams if sortBy has genuinely changed
    // This effect should handle updating the URL when sortBy changes
    if (sortBy !== prevSortByRef.current) {
      const newParams = new URLSearchParams(searchParams);
      if (sortBy && sortBy !== "name") {
        newParams.set("sort_by", sortBy);
      } else {
        newParams.delete("sort_by");
      }
      newParams.set("page", "1"); // Always reset to page 1 on sort by change
      setSearchParams(newParams);
      prevSortByRef.current = sortBy; // Update the ref
    }
  }, [sortBy, searchParams, setSearchParams]); // Keep searchParams in dependencies for the latest version

  const handleViewDetails = (personId: number) => {
    navigate(`/people/${personId}`);
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    // Explicitly invalidate 'people' query when page changes to ensure refetch
    queryClient.invalidateQueries({ queryKey: ["people"] });
    window.scrollTo(0, 0);
  };

  const handleSortChange = (column: "name" | "image_count") => {
    let newSortBy: SortByValue;
    if (sortBy === column) {
      newSortBy = `-${column}`;
    } else if (sortBy === `-${column}`) {
      newSortBy = "name";
    } else {
      newSortBy = column;
    }
    setSortBy(newSortBy);
  };

  const getSortIcon = (column: "name" | "image_count") => {
    if (sortBy === column) {
      return <i className="bi bi-caret-up-fill ms-1"></i>;
    } else if (sortBy === `-${column}`) {
      return <i className="bi bi-caret-down-fill ms-1"></i>;
    }
    return null;
  };

  // Calculate total pages
  const totalPages = data ? Math.ceil(data.count / pageSize) : 0;

  if (isLoading || isFetching) {
    return (
      <Container className="mt-4">
        <p>Loading people...</p>
      </Container>
    );
  }

  if (isError) {
    console.error("Error fetching people:", error);
    return (
      <Container className="mt-4">
        <p className="text-danger">Error: {(error as Error).message}</p>
      </Container>
    );
  }

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
                        <span>{truncateString(person.description, 50)}</span>
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

          <PaginationComponent
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />

          <div className="mt-3 text-muted">
            Showing {offset + 1}-{Math.min(offset + pageSize, data.count)} of {data.count} people
          </div>
        </>
      )}
    </Container>
  );
};

export default PeoplePage;
