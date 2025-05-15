import React, { useEffect, useState } from "react";
import { Container, Row, Col, Button, Spinner, Card, ListGroup } from "react-bootstrap";
import {
  imageGetDate,
  imageGetLocation,
  imageGetMetadata,
  imageGetPeople,
  imageGetPets,
} from "../api";
import { useParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import BoundingBoxOverlay from "../components/image/BoundingBoxOverlay";
import type { PersonInImageSchemaOut } from "../api";
import type { ImageMetadataSchema } from "../api";
import type { ImageLocationSchema } from "../api";
import type { ImageDateSchema } from "../api";
import type { PetInImageSchemaOut } from "../api";
import { Helmet } from "react-helmet-async";

const ImageDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const imageId = parseInt(id || "0", 10);
  const { profile } = useAuth(); // Get user profile with timezone

  const [metadata, setMetadata] = useState<ImageMetadataSchema | null>(null);
  const [location, setLocation] = useState<ImageLocationSchema | null>(null);
  const [dateInfo, setDateInfo] = useState<ImageDateSchema | null>(null);
  const [people, setPeople] = useState<PersonInImageSchemaOut[]>([]);
  const [pets, setPets] = useState<PetInImageSchemaOut[]>([]);
  const [showPeople, setShowPeople] = useState(false);
  const [showPets, setShowPets] = useState(false);
  const [loading, setLoading] = useState(true);
  const [canEdit, setCanEdit] = useState(false); // This would be set based on user permissions

  useEffect(() => {
    if (!imageId) return;

    const loadData = async () => {
      setLoading(true);
      try {
        const id = +imageId;
        const [meta, loc, date, ppl, pets] = await Promise.all([
          imageGetMetadata({ path: { image_id: id } }),
          imageGetLocation({ path: { image_id: id } }),
          imageGetDate({ path: { image_id: id } }),
          imageGetPeople({ path: { image_id: id } }),
          imageGetPets({ path: { image_id: id } }),
        ]);

        setMetadata(meta.data === undefined ? null : meta.data);
        setLocation(loc.data === undefined ? null : loc.data);
        setDateInfo(date.data === undefined ? null : date.data);
        setPeople(ppl.data === undefined ? [] : ppl.data);
        setPets(pets.data === undefined ? [] : pets.data);

        // Check if user has edit permissions (this would be implemented based on your auth system)
        setCanEdit(true); // Placeholder - replace with actual permission check
      } catch (error) {
        console.error("Error loading image data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [imageId]);

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
  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return "Not available";
    try {
      const date = new Date(dateString);

      // Use the user's timezone if available
      if (profile?.timezone_name) {
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

  if (loading) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
      </Container>
    );
  }

  if (!metadata) {
    return (
      <Container className="mt-5">
        <div className="alert alert-warning">Image data not available or could not be loaded.</div>
      </Container>
    );
  }

  const {
    full_size_url,
    orientation,
    original_height,
    original_width,
    title,
    file_size,
    description,
    created_at,
    updated_at,
    original_checksum,
    phash,
    image_fs_id,
    original_path,
  } = metadata;

  return (
    <Container fluid className="py-4">
      <Helmet>
        <title>Memoria - Image: {title}</title>
      </Helmet>
      <Row className="mb-4">
        {/* Image Section (Left Column) */}
        <Col md={8}>
          {full_size_url ? (
            <Card>
              <Card.Body className="p-1 text-center">
                <div
                  id="imageContainer"
                  style={{ position: "relative", display: "inline-block" }}
                  data-orientation={orientation}
                >
                  <img
                    id="mainImage"
                    src={full_size_url}
                    alt={title || "Image"}
                    className="img-fluid rounded"
                    style={{ maxHeight: "70vh", width: "auto" }}
                  />
                  {showPeople && people && people.length > 0 && (
                    <BoundingBoxOverlay
                      boxes={people}
                      orientation={orientation || 1}
                      color="rgba(0, 123, 255, 0.5)" // Blue with opacity
                      labelKey="name"
                    />
                  )}
                  {showPets && pets && pets.length > 0 && (
                    <BoundingBoxOverlay
                      boxes={pets}
                      orientation={orientation || 1}
                      color="rgba(255, 193, 7, 0.5)" // Amber/Yellow with opacity
                      labelKey="name"
                    />
                  )}
                </div>
              </Card.Body>
              <Card.Footer className="d-flex justify-content-between flex-wrap">
                <span>
                  {original_width}x{original_height} px
                </span>
                <span>{file_size ? formatBytes(file_size) : "Unknown size"}</span>
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
              <h5 className="card-title">Title: {title || "Untitled Image"}</h5>

              {description ? (
                <p className="card-text">{description}</p>
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
                <span className="text-muted"> {formatDate(created_at)}</span>
              </p>

              <p className="small mb-1">
                <strong>Updated:</strong>
                <span className="text-muted"> {formatDate(updated_at)}</span>
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
                      {original_checksum
                        ? `${original_checksum.slice(0, 16)}...`
                        : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Perceptual Hash:</strong>
                    <span className="text-monospace text-muted"> {phash || "Not available"}</span>
                  </p>
                  <p className="small mb-1">
                    <strong>Orientation:</strong>
                    <span className="text-muted">
                      {" "}
                      {getOrientationDisplay(orientation)} ({orientation})
                    </span>
                  </p>
                </Col>
                <Col md={6}>
                  <p className="small mb-1">
                    <strong>File Size:</strong>
                    <span className="text-muted">
                      {" "}
                      {file_size ? formatBytes(file_size) : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Dimensions:</strong>
                    <span className="text-muted">
                      {" "}
                      {original_width && original_height
                        ? `${original_width}x${original_height} pixels`
                        : "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>ID:</strong>
                    <span className="text-monospace text-muted">
                      {" "}
                      {image_fs_id || "Not available"}
                    </span>
                  </p>
                  <p className="small mb-1">
                    <strong>Original File:</strong>{" "}
                    <span
                      className="text-monospace text-muted text-truncate d-inline-block align-baseline"
                      style={{ maxWidth: "100%" }}
                    >
                      {original_path || "Not available"}
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

// Helper function to convert orientation number to display string
function getOrientationDisplay(orientation: number | null | undefined): string {
  if (orientation === null || orientation === undefined) return "Unknown";

  const orientationMap: Record<number, string> = {
    1: "Normal",
    2: "Mirror horizontal",
    3: "Rotate 180",
    4: "Mirror vertical",
    5: "Mirror horizontal and rotate 270 CW",
    6: "Rotate 90 CW",
    7: "Mirror horizontal and rotate 90 CW",
    8: "Rotate 270 CW",
  };

  return orientationMap[orientation] || `Orientation ${orientation}`;
}

export default ImageDetailPage;
