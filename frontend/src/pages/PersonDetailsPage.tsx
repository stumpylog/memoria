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
  // Initialize totalImageCount to undefined to distinguish between 'not yet loaded' and 'zero'
  const [totalImageCount, setTotalImageCount] = useState<number | undefined>(undefined);

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
      // Return data or null, do NOT update local state here
      return response?.data || null;
    },
    enabled: isValidId,
    staleTime: 60, // Keep data fresh for 1 minute
  });

  // Use useEffect to update totalImageCount when person data changes
  useEffect(() => {
    if (person) {
      // Update totalImageCount when person data is successfully fetched/available (including from cache)
      setTotalImageCount(person.image_count || 0);
    } else if (!isLoadingPerson && !isErrorPerson && isValidId) {
      // If person is null after loading and no error, it means person not found
      // Set count to 0 in this case
      setTotalImageCount(0);
    } else if (isErrorPerson) {
      // Optionally handle error state for count display, e.g., set to undefined or show error indicator
      setTotalImageCount(undefined); // Revert to undefined on error or loading, shows "Loading..."
    }
  }, [person, isLoadingPerson, isErrorPerson, isValidId]); // Depend on person data and query states

  // 2. Query for Paginated Image IDs
  const {
    data: paginatedImageObjects,
    isLoading: isLoadingPaginatedImageObjects,
    isError: isErrorPaginatedImageObjects,
    error: paginatedImageObjectsError,
  } = useQuery<PersonImageOutSchema[], Error, PersonImageOutSchema[], readonly unknown[]>({
    queryKey: ["person-image-ids", personId, limit, offset],
    queryFn: async (): Promise<PersonImageOutSchema[]> => {
      const response = await getPersonImages({
        path: { person_id: personId! },
        query: { limit, offset },
      });

      const pagedData: PagedPersonImageOutSchema | undefined = response?.data;
      const actualImageObjects: PersonImageOutSchema[] | undefined = pagedData?.items;

      if (Array.isArray(actualImageObjects)) {
        return actualImageObjects;
      }

      console.warn(
        "Paginated image data from API is not in the expected structure (e.g., response.data.items). Response data:",
        response?.data,
      );
      return [];
    },
    // Enabled if person data is loaded and valid, regardless of initial totalImageCount state
    enabled: isValidId && !!person && limit > 0,
    staleTime: 5 * 60 * 1000, // Also set staleTime for image IDs
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
      return imageResults.filter((item): item is ImageThumbnailSchema => item !== null);
    },
    enabled: currentImageIds.length > 0,
    staleTime: 5 * 60 * 1000, // Also set staleTime for thumbnails
  });

  // Handle Loading States for Person Details
  if (isLoadingPerson && !person) {
    // Only show initial loader if no person data is available
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading person details...</span>
        </Spinner>
        <p>Loading person details...</p>
      </Container>
    );
  }

  // Handle Error States for Person Details
  if (isErrorPerson) {
    return (
      <Container className="mt-4">
        <p className="text-danger">
          Error fetching person: {personError?.message || "An unknown error occurred."}
        </p>
      </Container>
    );
  }

  // Handle Person Not Found
  if (!person && !isLoadingPerson) {
    // Check if not loading and person data is null
    return (
      <Container className="mt-4">
        <p className="text-danger">Person with ID {personId} not found.</p>
      </Container>
    );
  }

  // If person data is still loading but we have cached data, proceed to render with cached data
  // The `person` variable will hold the cached data in this case.

  // Pagination handlers
  const handleNextPage = () => {
    // Only proceed if totalImageCount is defined (meaning person data has loaded)
    if (totalImageCount !== undefined && offset + limit < totalImageCount) {
      setOffset(offset + limit);
    }
  };

  const handlePreviousPage = () => {
    // Only proceed if totalImageCount is defined
    if (totalImageCount !== undefined) {
      setOffset(Math.max(0, offset - limit));
    }
  };

  const isLoadingAnyImageData = isLoadingPaginatedImageObjects || isLoadingImages;
  const isErrorAnyImageData = isErrorPaginatedImageObjects || isErrorImages;
  const anyImageError = paginatedImageObjectsError || imagesError;

  return (
    <Container className="mt-4">
      <Helmet>
        <title>Memoria - {person?.name || "Loading..."}</title>{" "}
        {/* Use optional chaining for title */}
      </Helmet>
      <h2>{person?.name || "Loading..."}</h2> {/* Use optional chaining for name */}
      {person?.description && <p>{person.description}</p>}{" "}
      {/* Use optional chaining for description */}
      <hr className="my-4" />
      {/* Show loading indicator for count until totalImageCount is defined */}
      <h3>Images ({totalImageCount !== undefined ? totalImageCount : "Loading..."})</h3>
      {/* Conditional rendering for image display area */}
      {isLoadingAnyImageData && !images ? ( // Show spinner if image data is loading and no images are currently displayed
        <Container className="mt-4 text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading images...</span>
          </Spinner>
          <p>Loading images...</p>
        </Container>
      ) : isErrorAnyImageData ? ( // Show error if image data failed to load
        <p className="text-warning">
          Could not load images.
          {anyImageError?.message}
        </p>
      ) : images && images.length > 0 ? ( // Render ImageWall if images array has data
        <>
          <ImageWall
            images={images} // `images` is guaranteed non-null/undefined here
            onImageClick={(imgId) => navigate(`/images/${imgId}`)}
            columns={4}
          />
          {/* Only show pagination if totalImageCount is known and there's more than one page */}
          {totalImageCount !== undefined && totalImageCount > limit && (
            <Row className="mt-4 mb-4 justify-content-center">
              {/* Pagination buttons */}
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
                  disabled={
                    totalImageCount === undefined ||
                    offset + limit >= totalImageCount ||
                    isLoadingAnyImageData
                  }
                >
                  Next
                </Button>
              </Col>
            </Row>
          )}
        </>
      ) : totalImageCount !== undefined &&
        totalImageCount === 0 &&
        !isLoadingAnyImageData &&
        !isErrorAnyImageData ? (
        // Show "No images" message ONLY if total count is known to be 0, loading is complete, and no error
        <p>No images found for this person.</p>
      ) : (
        // Fallback case: totalImageCount might be undefined or other unexpected state after initial load attempt
        // This indicates image information is still pending or could not be determined.
        <p>Loading image information...</p>
      )}
    </Container>
  );
};

export default PersonDetailsPage;
