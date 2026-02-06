// src/pages/PetsPage.tsx

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import {
  Button,
  Container,
  Form,
  FormControl,
  InputGroup,
  OverlayTrigger,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { PetReadSchemaOut, PetTypeChoices } from "../api";

import { getAllPetsOptions } from "../api/@tanstack/react-query.gen";
import PaginationComponent from "../components/common/PaginationComponent";
import ThemedSelect from "../components/common/ThemedSelect";
import { useAuth } from "../hooks/useAuth";
import { truncateString } from "../utils/truncateString";

// Define a runtime constant for pet types here, outside the API generated file
const PET_TYPE_OPTIONS = ["cat", "dog", "horse"] as const;

// Define a type alias for the allowed sort_by values for pets
type SortByValue = "name" | "-name" | "image_count" | "-image_count";

const PetsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  const [searchTerm, setSearchTerm] = useState(searchParams.get("pet_name") || "");
  const [selectedPetType, setSelectedPetType] = useState<PetTypeChoices | null>(
    (searchParams.get("pet_type") as PetTypeChoices) || null,
  );

  const searchInputRef = useRef<HTMLInputElement>(null);

  // State for sorting: Stores the raw sort_by string (e.g., "name", "-name", "image_count", "-image_count")
  // The default sort when nothing is specified or cleared is "name" (ascending).
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

  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10;

  const offset = (currentPage - 1) * pageSize;

  const { data, isLoading, isError, error } = useQuery({
    ...getAllPetsOptions({
      query: {
        limit: pageSize,
        offset: offset,
        // Pass null if selectedPetType is null or an empty string, otherwise pass the value
        pet_type: selectedPetType || null,
        pet_name: searchTerm || undefined,
        sort_by: sortBy,
      },
    }),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });

  const prevSearchTermRef = useRef(searchTerm);
  const prevSortByRef = useRef(sortBy);

  useEffect(() => {
    // Only update searchParams if searchTerm has genuinely changed
    if (searchTerm !== prevSearchTermRef.current) {
      const newParams = new URLSearchParams(searchParams);
      if (searchTerm) {
        newParams.set("pet_name", searchTerm);
      } else {
        newParams.delete("pet_name");
      }
      // Handle null/empty string for selectedPetType in URL params
      if (selectedPetType === null) {
        newParams.delete("pet_type");
      } else {
        newParams.set("pet_type", selectedPetType);
      }
      newParams.set("page", "1");
      setSearchParams(newParams);
      prevSearchTermRef.current = searchTerm; // Update the ref
    }
  }, [searchTerm, selectedPetType, searchParams, setSearchParams]);

  // Effect for sortBy changes, only runs when sortBy state itself changes significantly
  useEffect(() => {
    // Only update searchParams if sortBy has genuinely changed
    if (sortBy !== prevSortByRef.current) {
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
      prevSortByRef.current = sortBy;
    }
  }, [sortBy, searchParams, setSearchParams]);

  const handleViewDetails = (petId: number) => {
    navigate(`/pets/${petId}`);
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

  const totalPages = data ? Math.ceil(data.count / pageSize) : 0;

  if (isLoading) {
    return (
      <Container className="mt-4">
        <p>Loading pets...</p>
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

  // Options for react-select Pet Type filter using the local constant
  const petTypeOptions = PET_TYPE_OPTIONS.map((type) => ({
    value: type,
    label: type.charAt(0).toUpperCase() + type.slice(1),
  }));

  return (
    <Container className="mt-4">
      <title>Memoria - Pets</title>
      <h2 className="mb-4">Pets List</h2>

      <InputGroup className="mb-3">
        <FormControl
          placeholder="Search by pet name..."
          aria-label="Search by pet name"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          ref={searchInputRef}
        />
        <Button variant="outline-secondary" disabled>
          <i className="bi bi-search"></i>
        </Button>
      </InputGroup>

      <div className="mb-3">
        <Form.Label>Filter by Pet Type:</Form.Label>
        <ThemedSelect<{ value: string; label: string }>
          options={[{ value: "", label: "All Types" }, ...petTypeOptions]}
          value={
            selectedPetType
              ? {
                  value: selectedPetType,
                  label: selectedPetType.charAt(0).toUpperCase() + selectedPetType.slice(1),
                }
              : { value: "", label: "All Types" }
          }
          onChange={(option) =>
            setSelectedPetType(option ? (option.value as PetTypeChoices) : null)
          }
        />
      </div>

      {(!data || data.items.length === 0) && <p>No pets found matching your criteria.</p>}

      {data && data.items.length > 0 && (
        <>
          <Table striped bordered hover responsive className="mt-3">
            <thead>
              <tr>
                <th onClick={() => handleSortChange("name")} style={{ cursor: "pointer" }}>
                  Name {getSortIcon("name")}
                </th>
                <th>Description</th>
                <th>Type</th>
                <th onClick={() => handleSortChange("image_count")} style={{ cursor: "pointer" }}>
                  Image Count {getSortIcon("image_count")}
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((pet: PetReadSchemaOut) => (
                <tr key={pet.id}>
                  <td>{pet.name}</td>
                  <td>
                    {pet.description && pet.description.length > 50 ? (
                      <OverlayTrigger
                        placement="top"
                        delay={{ show: 250, hide: 400 }}
                        overlay={<Tooltip id={`tooltip-${pet.id}`}>{pet.description}</Tooltip>}
                      >
                        <span>{truncateString(pet.description, 50)}</span>
                      </OverlayTrigger>
                    ) : (
                      pet.description || "N/A"
                    )}
                  </td>
                  <td>
                    {/* Safely display pet_type, handling null */}
                    {pet.pet_type
                      ? pet.pet_type.charAt(0).toUpperCase() + pet.pet_type.slice(1)
                      : "N/A"}
                  </td>
                  <td>{pet.image_count}</td>
                  <td>
                    <Button variant="primary" size="sm" onClick={() => handleViewDetails(pet.id)}>
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
            Showing {offset + 1}-{Math.min(offset + pageSize, data.count)} of {data.count} pets
          </div>
        </>
      )}
    </Container>
  );
};

export default PetsPage;
