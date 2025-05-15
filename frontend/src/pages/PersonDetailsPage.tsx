// src/pages/PersonDetailsPage.tsx

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import type {
  PersonDetailOutSchema,
  ImageThumbnailSchema,
  PersonImageOutSchema,
  PagedPersonImageOutSchema,
} from "../api";
import { getPersonDetail, imageGetThumbInfo, getPersonImages } from "../api";
import { Container, Button, Row, Col, Spinner } from "react-bootstrap";
import ImageWall from "../components/image/ImageWall";
import { Helmet } from "react-helmet-async";
import { useAuth } from "../hooks/useAuth";

const PersonDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { profile } = useAuth();

  const personId = id ? parseInt(id, 10) : undefined;
  const isValidId = personId !== undefined && !isNaN(personId);

  const [offset, setOffset] = useState<number>(0);
  const [limit, setLimit] = useState<number>(profile?.items_per_page || 30);
  const [totalImageCount, setTotalImageCount] = useState<number>(0);

  useEffect(() => {
    if (profile?.items_per_page) {
      setLimit(profile.items_per_page);
      setOffset(0);
    }
  }, [profile]);

  // 1. Query for Person Details (includes image_count)
  const {
    data: person,
    isLoading: isLoadingPerson,
    isError: isErrorPerson,
    error: personError,
  } = useQuery<PersonDetailOutSchema | null, Error>({
    queryKey: ["person", personId],
    queryFn: async () => {
      if (!isValidId) throw new Error("Invalid person ID.");
      const response = await getPersonDetail({ path: { person_id: personId! } });
      if (response?.data) {
        // Use image_count from PersonDetailOutSchema for totalImageCount
        setTotalImageCount(response.data.image_count || 0);
        return response.data;
      }
      return null;
    },
    enabled: isValidId,
  });

  // 2. Query for Paginated Image IDs
  const {
    data: paginatedImageObjects,
    isLoading: isLoadingPaginatedImageObjects,
    isError: isErrorPaginatedImageObjects,
    error: paginatedImageObjectsError,
  } = useQuery<PersonImageOutSchema[], Error, PersonImageOutSchema[], readonly unknown[]>({
    queryKey: ["person-image-ids", personId, limit, offset],
    queryFn: async (): Promise<PersonImageOutSchema[]> => {
      // The `enabled` condition handles guards for personId, person, totalImageCount, limit.

      const response = await getPersonImages({
        // Type of 'response' is likely { data: PagedPersonImageOutSchema, ...other client props }
        path: { person_id: personId! },
        query: { limit, offset },
      });

      // Access the PagedPersonImageOutSchema from response.data
      const pagedData: PagedPersonImageOutSchema | undefined = response?.data;

      // Now extract the array of PersonImageOutSchema from pagedData.
      // COMMON PROPERTY NAMES: items, results, list, records, data.
      // Using 'items' as an assumption. PLEASE VERIFY THIS.
      const actualImageObjects: PersonImageOutSchema[] | undefined = pagedData?.items;

      if (Array.isArray(actualImageObjects)) {
        return actualImageObjects;
      }

      // Log a warning if the expected structure isn't found.
      console.warn(
        "Paginated image data from API is not in the expected structure (e.g., response.data.items). Response data:",
        response?.data,
      );
      return []; // Return empty array if data is not in the expected structure or if response/data is null/undefined.
    },
    enabled: isValidId && !!person && totalImageCount > 0 && limit > 0,
  });

  // Extract IDs for the next query
  const currentImageIds = paginatedImageObjects?.map((img) => img.id) || [];

  // 3. Query for Image Thumbnails based on Paginated IDs
  const {
    data: images,
    isLoading: isLoadingImages,
    isError: isErrorImages,
    error: imagesError,
  } = useQuery<ImageThumbnailSchema[] | null, Error>({
    queryKey: ["person-images-thumbnails", currentImageIds.join(",")], // Key depends on the current set of IDs
    queryFn: async () => {
      if (currentImageIds.length === 0) {
        return [];
      }
      const imagePromises = currentImageIds.map((imageId) =>
        imageGetThumbInfo({ path: { image_id: imageId } })
          .then((response) => response.data)
          .catch((imgErr) => {
            console.error(`Failed to fetch thumbnail for image ID ${imageId}:`, imgErr);
            return null;
          }),
      );
      const imageResults = await Promise.all(imagePromises);
      return imageResults.filter(
        (item): item is ImageThumbnailSchema => item !== null, // Type guard
      );
    },
    enabled: currentImageIds.length > 0,
  });

  // Handle Loading States
  // Show spinner while person details are loading
  if (isLoadingPerson) {
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading person details...</span>
        </Spinner>
        <p>Loading person details...</p>
      </Container>
    );
  }

  // Handle Error States for Person
  if (isErrorPerson) {
    return (
      <Container className="mt-4">
        <p className="text-danger">
          Error fetching person: {personError?.message || "An unknown error occurred."}
        </p>
      </Container>
    );
  }

  if (!person) {
    return (
      <Container className="mt-4">
        <p className="text-danger">Person with ID {personId} not found.</p>
      </Container>
    );
  }

  // Pagination handlers
  const handleNextPage = () => {
    if (offset + limit < totalImageCount) {
      setOffset(offset + limit);
    }
  };

  const handlePreviousPage = () => {
    setOffset(Math.max(0, offset - limit));
  };

  const isLoadingAnyImageData = isLoadingPaginatedImageObjects || isLoadingImages;
  const isErrorAnyImageData = isErrorPaginatedImageObjects || isErrorImages;
  const anyImageError = paginatedImageObjectsError || imagesError;

  return (
    <Container className="mt-4">
      <Helmet>
        <title>Memoria - {person.name}</title>
      </Helmet>
      <h2>{person.name}</h2>
      {person.description && <p>{person.description}</p>}
      <hr className="my-4" />
      <h3>Images ({totalImageCount})</h3>

      {/* Show spinner while image data is loading, but only if no images are currently displayed */}
      {isLoadingAnyImageData && !images ? (
        <Container className="mt-4 text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading images...</span>
          </Spinner>
          <p>Loading images...</p>
        </Container>
      ) : isErrorAnyImageData ? (
        <p className="text-warning">
          Could not load images.
          {anyImageError?.message}
        </p>
      ) : totalImageCount === 0 ? (
        <p>No images found for this person.</p>
      ) : (
        <>
          <ImageWall
            images={images || []}
            onImageClick={(imgId) => navigate(`/images/${imgId}`)}
            columns={4}
          />
          {totalImageCount > limit && ( // Only show pagination controls if there's more than one page
            <Row className="mt-4 mb-4 justify-content-center">
              <Col xs="auto">
                <Button
                  onClick={handlePreviousPage}
                  disabled={offset === 0 || isLoadingAnyImageData}
                >
                  Previous
                </Button>
              </Col>
              <Col xs="auto" className="d-flex align-items-center">
                <span>
                  Page {Math.floor(offset / limit) + 1} of {Math.ceil(totalImageCount / limit)}
                </span>
              </Col>
              <Col xs="auto">
                <Button
                  onClick={handleNextPage}
                  disabled={offset + limit >= totalImageCount || isLoadingAnyImageData}
                >
                  Next
                </Button>
              </Col>
            </Row>
          )}
        </>
      )}
    </Container>
  );
};

export default PersonDetailsPage;
