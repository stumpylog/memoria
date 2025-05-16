// src/pages/ImageDetailPage.tsx

import { useQueries } from "@tanstack/react-query";
import React, { useState } from "react";
import { Button, Col, Container, Row, Spinner } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router-dom";

import type {
  ImageDateSchema,
  ImageLocationSchema,
  ImageMetadataSchema,
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

  const [showPeople, setShowPeople] = useState(false);
  const [showPets, setShowPets] = useState(false);

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

  const metadata: ImageMetadataSchema | null = metadataRes.data?.data ?? null;
  const location: ImageLocationSchema | null = locationRes.data?.data ?? null;
  const dateInfo: ImageDateSchema | null = dateRes.data?.data ?? null;
  const people: PersonInImageSchemaOut[] = peopleRes.data?.data ?? [];
  const pets: PetInImageSchemaOut[] = petsRes.data?.data ?? [];

  const canEdit = true; // Replace with actual permission check later

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
          showPeople={showPeople}
          setShowPeople={setShowPeople}
          showPets={showPets}
          setShowPets={setShowPets}
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
          <ImagePeopleCard people={people} />

          {/* Pets Card */}
          <ImagePetsCard pets={pets} />

          {/* Edit Button */}
          {canEdit && (
            <div className="d-flex justify-content-end mb-4">
              <Button href={`/images/${imageId}/edit`} variant="primary">
                <i className="bi bi-pencil"></i> Edit
              </Button>
            </div>
          )}
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
