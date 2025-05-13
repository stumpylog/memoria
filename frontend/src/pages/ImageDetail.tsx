import React, { useEffect, useState } from "react"; // Import React
import { Container, Row, Col, Button, Spinner } from "react-bootstrap";
import {
  imageGetDate,
  imageGetLocation,
  imageGetMetadata,
  imageGetPeople,
  imageGetPets,
} from "../api"; // Adjust path as needed
import { useParams } from "react-router-dom";
import BoundingBoxOverlay from "../components/image/BoundingBoxOverlay";
import type { PersonInImageSchemaOut } from "../api";
import type { ImageMetadataSchema } from "../api";
import type { ImageLocationSchema } from "../api";
import type { ImageDateSchema } from "../api";
import type { PetInImageSchemaOut } from "../api";

const ImageDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const imageId = parseInt(id || '0', 10);

  const [metadata, setMetadata] = useState<ImageMetadataSchema | null>(null);
  const [location, setLocation] = useState<ImageLocationSchema | null>(null);
  const [dateInfo, setDateInfo] = useState<ImageDateSchema | null>(null);
  const [people, setPeople] = useState<PersonInImageSchemaOut[]>([]);
  const [pets, setPets] = useState<PetInImageSchemaOut[]>([]);
  const [showPeople, setShowPeople] = useState(true);
  const [showPets, setShowPets] = useState(true);

  useEffect(() => {
    console.log("Image is ", imageId);
    if (!imageId) return;
    const loadData = async () => {
      // Convert imageId to number for API calls
      const id = +imageId;
      const [meta, loc, date, ppl, pets] = await Promise.all([
        imageGetMetadata({"path": {"image_id": id}}),
        imageGetLocation({"path": {"image_id": id}}),
        imageGetDate({"path": {"image_id": id}}),
        imageGetPeople({"path": {"image_id": id}}),
        imageGetPets({"path": {"image_id": id}}),
      ]);
      setMetadata(meta.data);
      setLocation(loc.data);
      setDateInfo(date.data);
      setPeople(ppl.data);
      setPets(pets.data);
    };
    loadData();
  }, [imageId]); // Depend on imageId

  if (!metadata) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
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
  } = metadata;

  // Helper function to format file size (optional, but nice for display)
  const formatBytes = (bytes: number, decimals = 2): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };


  return (
    <Container fluid>
      <Row className="mt-4">
        <Col md={8} className="position-relative">
          <div className="image-container" style={{ position: "relative" }}>
            <img
              src={full_size_url}
              alt={title || 'Image'} // Add a fallback alt text
              className="img-fluid"
              style={{ width: "100%" }}
            />
            {showPeople && people && people.length > 0 && ( // Check if people array is not empty
              <BoundingBoxOverlay
                boxes={people}
                orientation={orientation}
                color="rgba(0, 123, 255, 0.5)" // Blue with opacity
                labelKey="name"
              />
            )}
            {showPets && pets && pets.length > 0 && ( // Check if pets array is not empty
              <BoundingBoxOverlay
                boxes={pets}
                orientation={orientation}
                color="rgba(255, 193, 7, 0.5)" // Amber/Yellow with opacity
                labelKey="name"
              />
            )}
          </div>
          {(people.length > 0 || pets.length > 0) && ( // Only show buttons if there are boxes to toggle
            <div className="mt-2">
              {people.length > 0 && (
                 <Button
                   variant={showPeople ? "primary" : "outline-primary"}
                   className="me-2"
                   onClick={() => setShowPeople(!showPeople)}
                 >
                   Toggle People ({people.length}) {/* Show count */}
                 </Button>
              )}
              {pets.length > 0 && (
                 <Button
                   variant={showPets ? "warning" : "outline-warning"}
                   onClick={() => setShowPets(!showPets)}
                 >
                   Toggle Pets ({pets.length}) {/* Show count */}
                 </Button>
              )}
            </div>
          )}
        </Col>

        <Col md={4}>
          <h3>{title || 'Untitled Image'}</h3> {/* Fallback title */}
          <p>{description}</p>

          <h5>Image Info</h5>
          <ul>
            <li>Size: {file_size ? formatBytes(file_size) : 'N/A'}</li> {/* Format file size */}
            <li>Dimensions: {original_width && original_height ? `${original_width}×${original_height}` : 'N/A'}</li>
            <li>Orientation: {orientation ?? 'N/A'}</li> {/* Use nullish coalescing */}
          </ul>

          <h5>Date Info</h5>
          {dateInfo ? ( // Conditional rendering
            <ul>
              <li>Date: {dateInfo.date || 'N/A'}</li>
              <li>Month valid: {dateInfo.month_valid ? "Yes" : "No"}</li>
              <li>Day valid: {dateInfo.day_valid ? "Yes" : "No"}</li>
            </ul>
          ) : <p>No date information available.</p>}


          <h5>Location</h5>
          {location ? ( // Conditional rendering
            <ul>
              {location.country_name && (
                <li>{location.country_name} ({location.country_code || 'N/A'})</li>
              )}
              {location.subdivision_name && (
                <li>{location.subdivision_name} ({location.subdivision_code || 'N/A'})</li>
              )}
              {location.city && <li>{location.city}</li>}
              {location.sub_location && <li>{location.sub_location}</li>}
              {!location.country_name && !location.subdivision_name && !location.city && !location.sub_location && (
                 <li>No location information available.</li>
              )}
            </ul>
          ) : <p>No location information available.</p>}

        </Col>
      </Row>
    </Container>
  );
};

export default ImageDetailPage;
