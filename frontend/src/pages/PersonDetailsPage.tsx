// src/pages/PersonDetailsPage.tsx

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom'; // To get ID from URL
import type { PersonDetailOutSchema } from '../api';
import type { ImageThumbnailSchema } from '../api';
import { getPersonDetail, imageGetThumbInfo } from '../api';
import { Container } from 'react-bootstrap';
import ImageWall from '../components/image/ImageWall';

const PersonDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>(); // Get ID from URL params

  const navigate = useNavigate();

  const [person, setPerson] = useState<PersonDetailOutSchema | null>(null);
  const [images, setImages] = useState<ImageThumbnailSchema[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      setPerson(null); // Clear previous data
      setImages(null); // Clear previous data

      if (!id) {
        setError(new Error("Person ID is missing from the URL."));
        setLoading(false);
        return;
      }

      const personId = parseInt(id, 10);

      if (isNaN(personId)) {
         setError(new Error(`Invalid person ID in URL: "${id}". ID must be a number.`));
         setLoading(false);
         return;
      }


      try {
        // Fetch person details
        const personData = await getPersonDetail({path: {person_id: personId}});

        if (!personData) {
             setError(new Error(`Person with ID ${personId} not found.`));
             setLoading(false);
             return;
        }

        setPerson(personData.data || null);

        // Fetch images if image_ids exist
        if (personData.data && personData.data.image_ids && personData.data.image_ids.length > 0) {
            const imagePromises = personData.data.image_ids.map(imageId =>
                imageGetThumbInfo({path: {image_id: imageId}})
                .then(response => response.data)
                 .catch(imgErr => {
                     console.error(`Failed to fetch thumbnail for image ID ${imageId}:`, imgErr);
                     // Return undefined or null for failed image fetches
                     return null;
                 })
            );

            // Use Promise.allSettled if you want to know the outcome of each promise
            // But for simplicity here, Promise.all with catch inside map is okay
            // if we just want to filter out the failed ones.
            const imageResults = await Promise.all(imagePromises);
            const successfulImages = imageResults.filter(item => item !== null) as ImageThumbnailSchema[];

            setImages(successfulImages);
        } else {
             setImages([]); // Set to empty array if no image_ids
        }

      } catch (err) {
        console.error("Error fetching person details or images:", err);
        if (err instanceof Error) {
          setError(err);
        } else {
          setError(new Error("An unknown error occurred while fetching details."));
        }
         setPerson(null);
         setImages(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [id]); // Re-run effect if the ID from the URL changes

  if (loading) {
    return (
      <Container className="mt-4">
        <p>Loading person details...</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="mt-4">
        <p className="text-danger">Error: {error.message}</p>
      </Container>
    );
  }

  if (!person) {
       // This case should ideally be caught by the error handling above,
       // but as a fallback:
      return (
         <Container className="mt-4">
            <p>Person details not found.</p>
         </Container>
      );
  }

  return (
    <Container className="mt-4">
      <h2>{person.name}</h2>
      {person.description && ( // Conditionally render description
        <p>{person.description}</p>
      )}

      {/* Visual separation */}
      <hr className="my-4"/>

      <h3>Images</h3>
       {/* Pass the fetched images to the ImageWall component */}
      <ImageWall images={images || []} onImageClick={(imageId) => {
                 navigate(`/images/${imageId}`);
             }} columns={4}/> {/* Ensure images is an array */}

    </Container>
  );
};

export default PersonDetailsPage;
