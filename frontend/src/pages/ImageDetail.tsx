import { useQueries } from "@tanstack/react-query";
import React, { useState } from "react";
import { Button, Card, Col, Container, ListGroup, Row, Spinner } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router-dom";

import type {
  ImageDateSchema,
  ImageLocationSchema,
  ImageMetadataSchema,
  PersonInImageSchemaOut,
  PetInImageSchemaOut,
  UserProfileOutSchema,
} from "../api";

import {
  imageGetDate,
  imageGetLocation,
  imageGetMetadata,
  imageGetPeople,
  imageGetPets,
} from "../api";
import BoundingBoxOverlay from "../components/image/BoundingBoxOverlay";
import { useAuth } from "../hooks/useAuth";

function getOrientationDisplay(orientation: number | null | undefined): string {
  const map: Record<number, string> = {
    1: "Normal",
    2: "Mirror horizontal",
    3: "Rotate 180",
    4: "Mirror vertical",
    5: "Mirror horizontal and rotate 270 CW",
    6: "Rotate 90 CW",
    7: "Mirror horizontal and rotate 90 CW",
    8: "Rotate 270 CW",
  };
  return orientation == null ? "Unknown" : map[orientation] || `Orientation ${orientation}`;
}

// Helper function to format file size
const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
};

// Format date helper with timezone support
const formatDate = (
  profile: UserProfileOutSchema | null,
  dateString: string | null | undefined,
): string => {
  if (!dateString) return "Not available";
  if (!profile) return dateString;
  try {
    const date = new Date(dateString);

    // Use the user's timezone if available
    if (profile.timezone_name) {
      return date.toLocaleString("en-US", {
        timeZone: profile.timezone_name,
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      });
    }

    // Fallback format if no timezone
    return date.toLocaleString();
  } catch (e) {
    return dateString;
  }
};

const formatImageDate = (dateInfo: ImageDateSchema): React.ReactNode => {
  if (!dateInfo.date) return <span className="fst-italic">Not available</span>;

  try {
    // Parse the original date
    const dateParts = dateInfo.date.split("-");
    if (dateParts.length !== 3) return dateInfo.date;

    let [year, month, day] = dateParts;

    // Replace month with XX if invalid
    if (!dateInfo.month_valid) {
      month = "XX";
    }

    // Replace day with YY if invalid
    if (!dateInfo.day_valid) {
      day = "YY";
    }

    return `${year}-${month}-${day}`;
  } catch (e) {
    return dateInfo.date;
  }
};

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
        <Col md={8}>
          {metadata.larger_size_url ? (
            <Card>
              <Card.Body className="p-1 text-center">
                <div
                  id="imageContainer"
                  style={{ position: "relative", display: "inline-block" }}
                  data-orientation={metadata.orientation}
                >
                  <img
                    id="mainImage"
                    src={metadata.larger_size_url}
                    alt={metadata.title || "Image"}
                    className="img-fluid rounded"
                    style={{ maxHeight: "70vh", width: "auto" }}
                  />
                  {showPeople && people && people.length > 0 && (
                    <BoundingBoxOverlay
                      boxes={people}
                      orientation={metadata.orientation || 1}
                      color="rgba(0, 123, 255, 0.5)" // Blue with opacity
                      labelKey="name"
                    />
                  )}
                  {showPets && pets && pets.length > 0 && (
                    <BoundingBoxOverlay
                      boxes={pets}
                      orientation={metadata.orientation || 1}
                      color="rgba(255, 193, 7, 0.5)" // Amber/Yellow with opacity
                      labelKey="name"
                    />
                  )}
                </div>
              </Card.Body>
              <Card.Footer className="d-flex justify-content-between flex-wrap">
                <span>
                  {metadata.original_width}x{metadata.original_height} px
                </span>
                <span>
                  {metadata.file_size ? formatBytes(metadata.file_size) : "Unknown size"}
                </span>
                <div className="d-flex">
                  {/* Toggle for People bounding boxes */}
                  <div className="form-check form-switch ms-3">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="personBoundingBoxToggle"
                      disabled={people.length === 0}
                      checked={showPeople}
                      onChange={() => setShowPeople(!showPeople)}
                    />
                    <label className="form-check-label" htmlFor="personBoundingBoxToggle">
                      Show People
                    </label>
                  </div>
                  {/* Toggle for Pets bounding boxes */}
                  <div className="form-check form-switch ms-3">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="petBoundingBoxToggle"
                      disabled={pets.length === 0}
                      checked={showPets}
                      onChange={() => setShowPets(!showPets)}
                    />
                    <label className="form-check-label" htmlFor="petBoundingBoxToggle">
                      Show Pets
                    </label>
                  </div>
                </div>
              </Card.Footer>
            </Card>
          ) : (
            <div className="alert alert-warning" role="alert">
              Full image not available.
            </div>
          )}
        </Col>

        {/* Info, People, Pets, Edit Section (Right Column) */}
        <Col md={4}>
          {/* Image Info Card */}
          <Card className="mb-4">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Image Info</h5>
            </Card.Header>
            <Card.Body>
              <h5 className="card-title">Title: {metadata.title || "Untitled Image"}</h5>

              {metadata.description ? (
                <p className="card-text">{metadata.description}</p>
              ) : (
                <p className="text-muted small">No description available.</p>
              )}

              <p className="mb-1">
                <strong>Date: </strong>
                {dateInfo ? (
                  <span className="text-muted"> {formatImageDate(dateInfo)}</span>
                ) : (
                  <span className="text-muted fst-italic"> Not available</span>
                )}
              </p>

              <p className="mb-1">
                <strong>Location: </strong>
                {location ? (
                  <span className="text-muted">
                    {location.sub_location && `${location.sub_location}, `}
                    {location.city && `${location.city}, `}
                    {location.subdivision_name && `${location.subdivision_name}, `}
                    {location.country_name && location.country_name}
                    {!location.sub_location &&
                      !location.city &&
                      !location.subdivision_name &&
                      !location.country_name && <span className="fst-italic">Not available</span>}
                  </span>
                ) : (
                  <span className="text-muted fst-italic"> Not available</span>
                )}
              </p>

              <hr />

              <p className="small mb-1">
                <strong>Created:</strong>
                <span className="text-muted"> {formatDate(profile, metadata.created_at)}</span>
              </p>

              <p className="small mb-1">
                <strong>Updated:</strong>
                <span className="text-muted"> {formatDate(profile, metadata.updated_at)}</span>
              </p>
            </Card.Body>
          </Card>

          {/* People Card */}
          {people.length > 0 && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">People</h5>
              </Card.Header>
              <ListGroup variant="flush">
                {people.map((personInImage, index) => (
                  <ListGroup.Item
                    key={index}
                    className="d-flex justify-content-between align-items-center"
                  >
                    {personInImage.name}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card>
          )}

          {/* Pets Card */}
          {pets.length > 0 && (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">Pets</h5>
              </Card.Header>
              <ListGroup variant="flush">
                {pets.map((petInImage, index) => (
                  <ListGroup.Item
                    key={index}
                    className="d-flex justify-content-between align-items-center"
                  >
                    {petInImage.name}
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card>
          )}

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

      {/* Tags Section */}

      {/* Technical Details Section */}
      <Row>
        <Col md={12} className="mb-4">
          <Card>
            <Card.Header>
              <h5 className="mb-0">Technical Details</h5>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <p className="small mb-1">
                    <strong>Original Checksum:</strong>
                    <span className="text-monospace text-muted">
                      {" "}
                      {metadata.original_checksum
                        ? `${metadata.original_checksum.slice(0, 16)}...`
                        : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Perceptual Hash:</strong>
                    <span className="text-monospace text-muted">
                      {" "}
                      {metadata.phash || "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Orientation:</strong>
                    <span className="text-muted">
                      {" "}
                      {getOrientationDisplay(metadata.orientation)} ({metadata.orientation})
                    </span>
                  </p>
                </Col>
                <Col md={6}>
                  <p className="small mb-1">
                    <strong>File Size:</strong>
                    <span className="text-muted">
                      {" "}
                      {metadata.file_size ? formatBytes(metadata.file_size) : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Dimensions:</strong>
                    <span className="text-muted">
                      {" "}
                      {metadata.original_width && metadata.original_height
                        ? `${metadata.original_width}x${metadata.original_height} pixels`
                        : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>ID:</strong>
                    <span className="text-monospace text-muted">
                      {" "}
                      {metadata.image_fs_id || "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Original File:</strong>{" "}
                    <span
                      className="text-monospace text-muted text-truncate d-inline-block align-baseline"
                      style={{ maxWidth: "100%" }}
                    >
                      {metadata.original_path || "Not available"}
                    </span>
                  </p>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ImageDetailPage;
