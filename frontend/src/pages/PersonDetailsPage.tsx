// src/pages/PersonDetailsPage.tsx

import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react"; // Import useRef
import { Button, Col, Container, Row, Spinner } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import type {
  ImagesPerPageChoices,
  ImageThumbnailSchema,
  PagedPersonImageOutSchema,
  PersonDetailOutSchema,
  PersonImageOutSchema,
} from "../api";

import { getPersonDetail, getPersonImages, imageGetThumbInfo } from "../api";
import ImageWall from "../components/image/ImageWall";
import { useAuth } from "../hooks/useAuth";
import { getGridColumns } from "../utils/getGridColums";

const PersonDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { profile } = useAuth();

  const personId = id ? parseInt(id, 10) : undefined;
  const isValidId = personId !== undefined && !isNaN(personId);

  // Use useSearchParams to manage offset and limit in the URL
  const [searchParams, setSearchParams] = useSearchParams();

  // Derive offset and limit from URL search params, with fallbacks
  // Use parseInt with radix 10 and provide default values
  const offset = parseInt(searchParams.get("offset") || "0", 10);
  // Initialize limit from URL or profile, but don't write to URL initially
  const initialLimit = parseInt(
    searchParams.get("limit") || String(profile?.items_per_page || 30),
    10,
  );
  const [limit, setLimit] = useState(initialLimit);

  // totalImageCount still needs useState as it's data from the API, not UI state directly
  const [totalImageCount, setTotalImageCount] = useState<number | undefined>(undefined);

  // Ref to track if it's the initial render
  const isInitialRender = useRef(true);

  // Effect to sync component's limit state with user profile's items_per_page
  // This runs on initial load and when profile or searchParams change.
  useEffect(() => {
    const profileLimit = profile?.items_per_page || 30;
    const urlLimitParam = searchParams.get("limit");
    const urlLimit = urlLimitParam ? parseInt(urlLimitParam, 10) : undefined;

    // Update component's internal limit state based on profile or URL if present
    if (profile && profileLimit !== limit) {
      setLimit(profileLimit);
    } else if (urlLimit !== undefined && urlLimit !== limit) {
      setLimit(urlLimit);
    } else if (urlLimit === undefined && profileLimit !== limit && isInitialRender.current) {
      // On initial render, if no URL limit and profile limit is different,
      // set component limit to profile limit but don't write to URL yet.
      setLimit(profileLimit);
    }

    // After initial render, if the component's limit (derived from profile/default)
    // is different from the URL's limit (which might be absent), update the URL
    // using replace: true to avoid adding to history on subsequent profile loads.
    if (!isInitialRender.current && profile && profileLimit !== urlLimit) {
      setSearchParams(
        (prevParams) => {
          const newParams = new URLSearchParams(prevParams);
          // Only set the limit param if it's different from the default to keep URLs cleaner
          if (profileLimit !== 30) {
            // Assuming 30 is the common default
            newParams.set("limit", String(profileLimit));
          } else {
            newParams.delete("limit"); // Remove if it's the default
          }
          return newParams;
        },
        { replace: true },
      );
    }

    // Mark initial render as complete
    isInitialRender.current = false;

    // Depend on profile and searchParams to react to external changes
    // Add setSearchParams as per React hook best practices
  }, [profile, searchParams, setSearchParams, limit]); // Added 'limit' to dependencies

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
      // Optionally handle error state for count display
      setTotalImageCount(undefined); // Revert to undefined on error or loading
    }
  }, [person, isLoadingPerson, isErrorPerson, isValidId]); // Depend on person data and query states

  // 2. Query for Paginated Image IDs
  const {
    data: paginatedImageObjects,
    isLoading: isLoadingPaginatedImageObjects,
    isError: isErrorPaginatedImageObjects,
    error: paginatedImageObjectsError,
  } = useQuery<PersonImageOutSchema[], Error, PersonImageOutSchema[], readonly unknown[]>({
    // queryKey depends on personId, limit, and offset (derived from URL)
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
    // Key depends on the current set of IDs
    queryKey: ["person-images-thumbnails", currentImageIds.join(",")],
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

  // Pagination handlers - update URL search params, pushing to history
  const handleNextPage = () => {
    // Only proceed if totalImageCount is defined and there's a next page
    if (totalImageCount !== undefined && offset + limit < totalImageCount) {
      setSearchParams((prevParams) => {
        const newParams = new URLSearchParams(prevParams);
        newParams.set("offset", String(offset + limit));
        // Also ensure the current limit is in the URL when navigating
        newParams.set("limit", String(limit));
        return newParams;
      }); // No { replace: true } - push new history entry
    }
  };

  const handlePreviousPage = () => {
    // Only proceed if totalImageCount is defined and not already on the first page
    if (totalImageCount !== undefined) {
      const newOffset = Math.max(0, offset - limit);
      setSearchParams((prevParams) => {
        const newParams = new URLSearchParams(prevParams);
        newParams.set("offset", String(newOffset));
        // Also ensure the current limit is in the URL when navigating
        newParams.set("limit", String(limit));
        return newParams;
      }); // No { replace: true } - push new history entry
    }
  };

  const isLoadingAnyImageData = isLoadingPaginatedImageObjects || isLoadingImages;
  const isErrorAnyImageData = isErrorPaginatedImageObjects || isErrorImages;
  const anyImageError = paginatedImageObjectsError || imagesError;

  // Calculate current page number
  const currentPage = Math.floor(offset / limit) + 1;
  // Calculate total pages, guarding against division by zero or undefined totalImageCount
  const totalPages =
    totalImageCount !== undefined && limit > 0 ? Math.ceil(totalImageCount / limit) : 0;

  return (
    <Container className="mt-4">
      <Helmet>
        <title>Memoria - {person?.name || "Loading..."}</title>
      </Helmet>
      <h2>{person?.name || "Loading..."}</h2>

      {/* Display description or "No description" */}
      {person?.description ? (
        <p>{person.description}</p>
      ) : (
        <p className="text-muted font-italic">No description</p>
      )}

      {/* Edit button */}
      {personId && ( // Ensure personId is available before rendering the button
        <Button onClick={() => navigate(`/people/${personId}/edit`)} className="mb-3">
          Edit
        </Button>
      )}

      <hr className="my-4" />

      <h3>Images ({totalImageCount !== undefined ? totalImageCount : "Loading..."})</h3>
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
      ) : images && images.length > 0 ? (
        <>
          <ImageWall
            images={images}
            onImageClick={(imgId) => navigate(`/images/${imgId}`)}
            columns={getGridColumns(limit as ImagesPerPageChoices)}
          />
          {totalImageCount !== undefined && totalImageCount > limit && (
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
                  Page {currentPage} of {totalPages}
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
        <p>No images found for this person.</p>
      ) : (
        <p>Loading image information...</p>
      )}
    </Container>
  );
};

export default PersonDetailsPage;
