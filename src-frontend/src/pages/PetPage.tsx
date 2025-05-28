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
  Pagination,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";
import Select from "react-select";

import type { PagedPetReadSchemaOut, PetReadSchemaOut, PetTypeChoices } from "../api";

import { getAllPets } from "../api"; // PET_TYPE_OPTIONS is defined locally now
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";

// Define a runtime constant for pet types here, outside the API generated file
const PET_TYPE_OPTIONS = ["cat", "dog", "horse"] as const;

const PetsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();
  const { effectiveTheme } = useTheme();
  const isDarkTheme = effectiveTheme === "dark";

  const [searchTerm, setSearchTerm] = useState(searchParams.get("pet_name") || "");
  const [selectedPetType, setSelectedPetType] = useState<PetTypeChoices | null>(
    (searchParams.get("pet_type") as PetTypeChoices) || null,
  );

  const searchInputRef = useRef<HTMLInputElement>(null);

  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10;

  const offset = (currentPage - 1) * pageSize;

  const { data, isLoading, isError, error } = useQuery<PagedPetReadSchemaOut>({
    queryKey: ["pets", currentPage, pageSize, searchTerm, selectedPetType],
    queryFn: async ({ signal }) => {
      const response = await getAllPets({
        query: {
          limit: pageSize,
          offset: offset,
          // Pass null if selectedPetType is null or an empty string, otherwise pass the value
          pet_type: selectedPetType || null,
          pet_name: searchTerm || undefined,
        },
        signal,
      });
      if (!response.data) {
        throw new Error("No data received from pets API.");
      }
      return response.data;
    },
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    const handler = setTimeout(() => {
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
    }, 500);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, selectedPetType, searchParams, setSearchParams]);

  const handleViewDetails = (petId: number) => {
    navigate(`/pets/${petId}`);
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    window.scrollTo(0, 0);
  };

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

  const truncateDescription = (text: string | undefined, maxLength: number) => {
    if (!text) return "N/A";
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  // Options for react-select Pet Type filter using the local constant
  const petTypeOptions = PET_TYPE_OPTIONS.map((type) => ({
    value: type,
    label: type.charAt(0).toUpperCase() + type.slice(1),
  }));

  const customStyles = {
    control: (provided: any, state: any) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff",
      borderColor: isDarkTheme ? "#495057" : "#ced4da",
      color: isDarkTheme ? "#f8f9fa" : "#212529",
      "&:hover": {
        borderColor: isDarkTheme ? "#6c757d" : "#adb5bd",
      },
      boxShadow: state.isFocused
        ? isDarkTheme
          ? "0 0 0 0.2rem rgba(108,117,125,.25)"
          : "0 0 0 0.2rem rgba(0,123,255,.25)"
        : null,
    }),
    singleValue: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    input: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    placeholder: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#adb5bd" : "#6c757d",
    }),
    menu: (provided: any) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff",
      borderColor: isDarkTheme ? "#495057" : "#ced4da",
    }),
    option: (provided: any, state: any) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? isDarkTheme
          ? "#007bff"
          : "#007bff"
        : state.isFocused
          ? isDarkTheme
            ? "#495057"
            : "#e9ecef"
          : isDarkTheme
            ? "#343a40"
            : "#fff",
      color: state.isSelected ? "#fff" : isDarkTheme ? "#f8f9fa" : "#212529",
      "&:active": {
        backgroundColor: isDarkTheme ? "#0056b3" : "#0056b3",
      },
    }),
  };

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
        <Select
          options={[{ value: "", label: "All Types" }, ...petTypeOptions]}
          value={
            selectedPetType
              ? {
                  value: selectedPetType,
                  label: selectedPetType.charAt(0).toUpperCase() + selectedPetType.slice(1),
                }
              : { value: "", label: "All Types" }
          }
          onChange={(option) => setSelectedPetType((option?.value as PetTypeChoices) || null)}
          styles={customStyles}
          theme={(currentTheme) => ({
            ...currentTheme,
            colors: {
              ...currentTheme.colors,
              primary: isDarkTheme ? "#007bff" : "#007bff",
              primary25: isDarkTheme ? "#495057" : "#e9ecef",
              neutral0: isDarkTheme ? "#343a40" : "#fff",
              neutral80: isDarkTheme ? "#f8f9fa" : "#212529",
              neutral20: isDarkTheme ? "#495057" : "#ced4da",
            },
          })}
        />
      </div>

      {(!data || data.items.length === 0) && <p>No pets found matching your criteria.</p>}

      {data && data.items.length > 0 && (
        <>
          <Table striped bordered hover responsive className="mt-3">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Type</th>
                <th>Image Count</th>
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
                        <span>{truncateDescription(pet.description, 50)}</span>
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

          {totalPages > 1 && (
            <div className="d-flex justify-content-center mt-4">{renderPaginationItems()}</div>
          )}

          <div className="mt-3 text-muted">
            Showing {offset + 1}-{Math.min(offset + pageSize, data.count)} of {data.count} pets
          </div>
        </>
      )}
    </Container>
  );
};

export default PetsPage;
