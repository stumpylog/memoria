// src/pages/ImageDetailPage.tsx

import { useQueries } from "@tanstack/react-query";
import React, { useEffect, useMemo, useState } from "react";
import { Button, Col, Container, Row, Spinner } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router-dom";

import type {
  ImageDateSchemaOut,
  ImageLocationSchemaOut,
  ImageMetadataSchemaOut,
  PersonInImageSchemaOut,
  PetInImageSchemaOut,
} from "../api";

import {
  imageGetDate,
  imageGetLocation,
  imageGetMetadata,
  imageGetPeople,
  imageGetPets,
} from "../api";
import ImageBasicInfoCard from "../components/image/ImageBasicInfoCard";
import ImageDisplaySection from "../components/image/ImageDisplaySection";
import ImagePeopleCard from "../components/image/ImagePeopleCard";
import ImagePetsCard from "../components/image/ImagePetsCard";
import ImageTechnicalDetails from "../components/image/ImageTechnicalDetails";
import { useAuth } from "../hooks/useAuth";

const ImageDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const imageId = parseInt(id || "0", 10);
  const { profile } = useAuth();

  // Global toggles for categories
  const [showPeople, setShowPeople] = useState(false);
  const [showPets, setShowPets] = useState(false);

  // State for individually toggled boxes (Maps box ID to boolean visibility)
  const [individualPeopleVisibility, setIndividualPeopleVisibility] = useState<
    Map<number, boolean>
  >(new Map());
  const [individualPetsVisibility, setIndividualPetsVisibility] = useState<Map<number, boolean>>(
    new Map(),
  );

  // Function to toggle visibility of a specific person's bounding box
  const togglePersonVisibility = (personId: number) => {
    setIndividualPeopleVisibility((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(personId, !(newMap.get(personId) ?? false)); // Toggle state, default to false if not set
      return newMap;
    });
  };

  // Function to toggle visibility of a specific pet's bounding box
  const togglePetVisibility = (petId: number) => {
    setIndividualPetsVisibility((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(petId, !(newMap.get(petId) ?? false)); // Toggle state, default to false if not set
      return newMap;
    });
  };

  const results = useQueries({
    queries: [
      {
        queryKey: ["metadata", imageId],
        queryFn: () => imageGetMetadata({ path: { image_id: imageId } }),
      },
      {
        queryKey: ["location", imageId],
        queryFn: () => imageGetLocation({ path: { image_id: imageId } }),
      },
      {
        queryKey: ["date", imageId],
        queryFn: () => imageGetDate({ path: { image_id: imageId } }),
      },
      {
        queryKey: ["people", imageId],
        queryFn: () => imageGetPeople({ path: { image_id: imageId } }),
      },
      {
        queryKey: ["pets", imageId],
        queryFn: () => imageGetPets({ path: { image_id: imageId } }),
      },
    ],
  });

  const isLoading = results.some((r) => r.isLoading);
  const isError = results.some((r) => r.isError);

  const [metadataRes, locationRes, dateRes, peopleRes, petsRes] = results;

  const metadata: ImageMetadataSchemaOut | null = metadataRes.data?.data ?? null;
  const location: ImageLocationSchemaOut | null = locationRes.data?.data ?? null;
  const dateInfo: ImageDateSchemaOut | null = dateRes.data?.data ?? null;

  // Memoize people and pets data
  const people: PersonInImageSchemaOut[] = useMemo(
    () => peopleRes.data?.data ?? [],
    [peopleRes.data?.data], // Recompute only if the underlying data changes
  );

  const pets: PetInImageSchemaOut[] = useMemo(
    () => petsRes.data?.data ?? [],
    [petsRes.data?.data], // Recompute only if the underlying data changes
  );

  // Reset individual visibility when people/pets data changes (e.g., on image ID change)
  useEffect(() => {
    setIndividualPeopleVisibility(new Map());
    setIndividualPetsVisibility(new Map());
    // Optionally, you could set the global toggles to false here too if desired
    setShowPeople(false);
    setShowPets(false);
  }, [people, pets]); // Now depends on the memoized arrays

  if (isLoading) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
      </Container>
    );
  }

  // If metadata is null or there's an error from any query
  if (!metadata || isError) {
    return (
      <Container className="mt-5">
        <div className="alert alert-warning">Image data not available or could not be loaded.</div>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <Helmet>
        <title>Memoria - Image: {metadata.title}</title>
      </Helmet>
      <Row className="mb-4">
        {/* Image Section (Left Column) */}
        <ImageDisplaySection
          metadata={metadata}
          people={people}
          pets={pets}
          showPeople={showPeople} // Global toggle state
          setShowPeople={setShowPeople} // Setter for global toggle
          showPets={showPets} // Global toggle state
          setShowPets={setShowPets} // Setter for global toggle
          individualPeopleVisibility={individualPeopleVisibility} // Individual visibility state
          individualPetsVisibility={individualPetsVisibility} // Individual visibility state
        />

        {/* Info, People, Pets, Edit Section (Right Column) */}
        <Col md={4}>
          {/* Image Info Card */}
          <ImageBasicInfoCard
            metadata={metadata}
            location={location}
            dateInfo={dateInfo}
            profile={profile}
          />

          {/* People Card */}
          <ImagePeopleCard
            people={people}
            individualVisibility={individualPeopleVisibility}
            toggleVisibility={togglePersonVisibility}
          />

          {/* Pets Card */}
          <ImagePetsCard
            pets={pets}
            individualVisibility={individualPetsVisibility}
            toggleVisibility={togglePetVisibility}
          />
        </Col>
      </Row>

      {/* Technical Details Section */}
      <Row>
        <ImageTechnicalDetails metadata={metadata} />
      </Row>
    </Container>
  );
};

export default ImageDetailPage;
