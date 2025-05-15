// src/pages/PersonDetailsPage.tsx

import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query"; // Import useQuery
import type { PersonDetailOutSchema } from "../api";
import type { ImageThumbnailSchema } from "../api";
import { getPersonDetail, imageGetThumbInfo } from "../api";
import { Container } from "react-bootstrap";
import ImageWall from "../components/image/ImageWall";
import { Helmet } from "react-helmet-async";

const PersonDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Validate and parse the ID
  const personId = id ? parseInt(id, 10) : undefined;
  const isValidId = personId !== undefined && !isNaN(personId);

  // 1. Query for Person Details
  const {
    data: person,
    isLoading: isLoadingPerson,
    isError: isErrorPerson,
    error: personError,
  } = useQuery<PersonDetailOutSchema | null, Error>({
    queryKey: ["person", personId], // Unique key for this query
    queryFn: async () => {
      if (!isValidId) {
        throw new Error("Invalid or missing person ID in URL.");
      }
      // Assuming getPersonDetail returns a response object with a 'data' property
      const response = await getPersonDetail({ path: { person_id: personId! } });
      if (!response || !response.data) {
        // You might throw an error here if a person is expected but not found
        // or return null if the API signals not found by returning data: null
        // For now, let's return the data property which could be null/undefined
        return response?.data || null;
      }
      return response.data;
    },
    enabled: isValidId, // Only run this query if the ID is valid
    // You can add staleTime, cacheTime, etc. here if needed
  });

  // Extract image_ids from the person data for the next query
  const imageIds = person?.image_ids || [];

  // 2. Query for Images related to the Person
  const {
    data: images,
    isLoading: isLoadingImages,
    isError: isErrorImages,
    error: imagesError,
  } = useQuery<ImageThumbnailSchema[] | null, Error>({
    queryKey: ["person-images", personId, imageIds], // Key depends on person ID and image IDs
    queryFn: async () => {
      if (imageIds.length === 0) {
        return []; // No images to fetch
      }
      const imagePromises = imageIds.map((imageId) =>
        imageGetThumbInfo({ path: { image_id: imageId } })
          .then((response) => response.data)
          .catch((imgErr) => {
            console.error(`Failed to fetch thumbnail for image ID ${imageId}:`, imgErr);
            return null; // Return null for failed fetches
          }),
      );

      const imageResults = await Promise.all(imagePromises);
      // Filter out any failed image fetches
      const successfulImages = imageResults.filter(
        (item) => item !== null,
      ) as ImageThumbnailSchema[];

      return successfulImages;
    },
    // This query depends on the person data being successfully fetched AND having image IDs
    enabled: !!person && imageIds.length > 0,
    // The query will refetch if imageIds changes (though this is unlikely for a given person)
    // If imageIds were to change dynamically for the same person ID,
    // react-query would automatically refetch this query due to the key change.
  });

  // Handle Loading States
  if (isLoadingPerson || (person && isLoadingImages)) {
    return (
      <Container className="mt-4">
        <p>Loading person details...</p>
      </Container>
    );
  }

  // Handle Error States
  if (isErrorPerson) {
    return (
      <Container className="mt-4">
        <p className="text-danger">
          Error fetching person: {personError?.message || "An unknown error occurred."}
        </p>
      </Container>
    );
  }

  // Handle case where person data was fetched but is null (e.g., 404 Not Found from API if getPersonDetail returns data: null)
  // Or the initial check for invalid ID failed.
  if (!person) {
    // If isValidId is false, personError should already be set.
    // If isValidId is true but person is null, it means the API returned no data for the ID.
    const displayError = !isValidId
      ? personError // Use the error set during initial validation
      : new Error(`Person with ID ${personId} not found.`); // Or a new error for 404 case

    return (
      <Container className="mt-4">
        <p className="text-danger">Error: {displayError ? displayError.message : "Unknown"}</p>
      </Container>
    );
  }

  // Handle Error State for Images (if person data was fetched successfully)
  if (isErrorImages) {
    // You might choose to render the person details and show an error message for images
    console.error("Error fetching images:", imagesError);
    // Option 1: Render person details and show an image error
    // Option 2: Show a full error page (less common if person data is available)
    // We'll proceed to render the page and potentially show an error message within the image section or just log it.
    // For this example, we'll proceed and the ImageWall might just be empty or show a loading/error state itself if it handles that.
    // Let's add a simple error message below the "Images" heading.
  }

  // If we reach here, person data is successfully loaded.
  // images data might be loading, errored, empty, or loaded.

  return (
    <Container className="mt-4">
      <Helmet>
        <title>Memoria - {person.name}</title>
      </Helmet>
      <h2>{person.name}</h2>
      {person.description && <p>{person.description}</p>}
      <hr className="my-4" />
      <h3>Images</h3>

      {/* Handle image loading/error states within the image section */}
      {isLoadingImages ? (
        <p>Loading images...</p>
      ) : isErrorImages ? (
        <p className="text-warning">Could not load all images. {imagesError?.message}</p> // Use warning for less critical error
      ) : (
        // Render ImageWall only when images data is available (could be an empty array)
        <ImageWall
          images={images || []} // Ensure images is always an array
          onImageClick={(imageId) => {
            navigate(`/images/${imageId}`);
          }}
          columns={4}
        />
      )}
    </Container>
  );
};

export default PersonDetailsPage;
