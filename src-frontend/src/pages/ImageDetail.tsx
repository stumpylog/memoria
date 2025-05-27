// src/pages/ImageDetailPage.tsx

import { useQueries } from "@tanstack/react-query";
import React, { useEffect, useMemo, useState } from "react";
import { Col, Container, Row, Spinner } from "react-bootstrap";
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
import DateEditModal from "../components/image/DateEditModal";
import GroupPermissionsModal from "../components/image/GroupPermissionsModal"; // New import
import ImageBasicInfoCard from "../components/image/ImageBasicInfoCard";
import ImageDisplaySection from "../components/image/ImageDisplaySection";
import ImagePeopleCard from "../components/image/ImagePeopleCard";
import ImagePetsCard from "../components/image/ImagePetsCard";
import ImageTechnicalDetails from "../components/image/ImageTechnicalDetails";
import LocationEditModal from "../components/image/LocationEditModal";
import MetadataEditModal from "../components/image/MetadataEditModal";
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

  // State for modal visibility
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showDateModal, setShowDateModal] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false); // New state

  // Function to toggle visibility of a specific person's bounding box
  const togglePersonVisibility = (personId: number) => {
    setIndividualPeopleVisibility((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(personId, !(newMap.get(personId) ?? false));
      return newMap;
    });
  };

  // Function to toggle visibility of a specific pet's bounding box
  const togglePetVisibility = (petId: number) => {
    setIndividualPetsVisibility((prevMap) => {
      const newMap = new Map(prevMap);
      newMap.set(petId, !(newMap.get(petId) ?? false));
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

  // Destructure results and get refetch functions
  const [metadataRes, locationRes, dateRes, peopleRes, petsRes] = results;

  const metadata: ImageMetadataSchemaOut | null = metadataRes.data?.data ?? null;
  const location: ImageLocationSchemaOut | null = locationRes.data?.data ?? null;
  const dateInfo: ImageDateSchemaOut | null = dateRes.data?.data ?? null;

  // Memoize people and pets data
  const people: PersonInImageSchemaOut[] = useMemo(
    () => peopleRes.data?.data ?? [],
    [peopleRes.data?.data],
  );

  const pets: PetInImageSchemaOut[] = useMemo(
    () => petsRes.data?.data ?? [],
    [petsRes.data?.data],
  );

  // Reset individual visibility when people/pets data changes
  useEffect(() => {
    setIndividualPeopleVisibility(new Map());
    setIndividualPetsVisibility(new Map());
    setShowPeople(false);
    setShowPets(false);
  }, [people, pets]);

  // Handlers for modal updates
  const handleLocationUpdated = () => {
    locationRes.refetch();
  };

  const handleDateUpdated = () => {
    dateRes.refetch();
  };

  const handleMetadataUpdated = () => {
    metadataRes.refetch();
  };

  const handlePermissionsUpdated = () => {
    // New handler
    metadataRes.refetch();
  };

  if (isLoading) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
      </Container>
    );
  }

  if (!metadata || isError) {
    return (
      <Container className="mt-5">
        <div className="alert alert-warning">Image data not available or could not be loaded.</div>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4">
      <title>Memoria - Image: {metadata.title}</title>
      <Row className="mb-4">
        {/* Image Section (Left Column) */}
        <ImageDisplaySection
          metadata={metadata}
          people={people}
          pets={pets}
          showPeople={showPeople}
          setShowPeople={setShowPeople}
          showPets={showPets}
          setShowPets={setShowPets}
          individualPeopleVisibility={individualPeopleVisibility}
          individualPetsVisibility={individualPetsVisibility}
        />

        {/* Info, People, Pets, Edit Section (Right Column) */}
        <Col md={4}>
          {/* Image Info Card */}
          <ImageBasicInfoCard
            metadata={metadata}
            location={location}
            dateInfo={dateInfo}
            profile={profile}
            setShowMetadataModal={setShowMetadataModal}
            setShowLocationModal={setShowLocationModal}
            setShowDateModal={setShowDateModal}
            setShowPermissionsModal={setShowPermissionsModal} // New prop
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

      {/* Edit Modals */}
      <MetadataEditModal
        show={showMetadataModal}
        onHide={() => setShowMetadataModal(false)}
        imageId={imageId}
        currentMetadata={metadata}
        onMetadataUpdated={handleMetadataUpdated}
      />

      <LocationEditModal
        show={showLocationModal}
        onHide={() => setShowLocationModal(false)}
        imageId={imageId}
        currentLocation={location}
        onLocationUpdated={handleLocationUpdated}
      />

      <DateEditModal
        show={showDateModal}
        onHide={() => setShowDateModal(false)}
        imageId={imageId}
        currentDate={dateInfo}
        onDateUpdated={handleDateUpdated}
      />

      <GroupPermissionsModal
        show={showPermissionsModal}
        onHide={() => setShowPermissionsModal(false)}
        imageId={imageId}
        currentMetadata={metadata}
        onPermissionsUpdated={handlePermissionsUpdated}
      />
    </Container>
  );
};

export default ImageDetailPage;
