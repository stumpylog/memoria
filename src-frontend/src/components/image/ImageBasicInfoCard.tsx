import React from "react";
import { Badge, Button, Card } from "react-bootstrap";
import { Nav } from "react-bootstrap";
import { Link } from "react-router-dom";

import type {
  ImageDateSchemaOut,
  ImageLocationSchemaOut,
  ImageMetadataSchemaOut,
  UserProfileOutSchema,
} from "../../api";

import { formatDate } from "../../utils/formatDate";

interface ImageBasicInfoCardProps {
  metadata: ImageMetadataSchemaOut;
  location: ImageLocationSchemaOut | null;
  dateInfo: ImageDateSchemaOut | null;
  profile: UserProfileOutSchema | null;
  // Add these props to control modal visibility from the parent
  setShowMetadataModal: (show: boolean) => void;
  setShowLocationModal: (show: boolean) => void;
  setShowDateModal: (show: boolean) => void;
  setShowPermissionsModal: (show: boolean) => void;
}

const formatImageDate = (dateInfo: ImageDateSchemaOut): React.ReactNode => {
  if (!dateInfo.comparison_date) return <span className="fst-italic">Not available</span>;

  try {
    // Parse the original date
    const dateParts = dateInfo.comparison_date.split("-");
    if (dateParts.length !== 3) return dateInfo.comparison_date;

    let [year, month, day] = dateParts;

    // Replace month with XX if invalid
    if (!dateInfo.month_valid) {
      month = "MM";
    }

    // Replace day with YY if invalid
    if (!dateInfo.day_valid) {
      day = "DD";
    }

    return `${year}-${month}-${day}`;
  } catch (e) {
    return dateInfo.comparison_date;
  }
};

const ImageBasicInfoCard: React.FC<ImageBasicInfoCardProps> = ({
  metadata,
  location,
  dateInfo,
  profile,
  // Destructure the new props
  setShowMetadataModal,
  setShowLocationModal,
  setShowDateModal,
  setShowPermissionsModal,
}) => {
  // Check if user has edit permissions
  const canEdit = metadata?.can_edit || false;

  return (
    <>
      <Card className="mb-4">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Image Info</h5>
          {canEdit && (
            <Button
              variant="outline-primary"
              size="sm"
              onClick={() => setShowMetadataModal(true)}
              title="Edit title and description"
            >
              <i className="bi bi-pencil"></i>
            </Button>
          )}
        </Card.Header>
        <Card.Body>
          <h5 className="card-title">Title: {metadata.title || "Untitled Image"}</h5>

          {metadata.description ? (
            <p className="card-text">{metadata.description}</p>
          ) : (
            <p className="text-muted small">No description available.</p>
          )}

          <div className="d-flex justify-content-between align-items-center mb-1">
            <div>
              <strong>Date: </strong>
              {dateInfo ? (
                <span className="text-muted"> {formatImageDate(dateInfo)}</span>
              ) : (
                <span className="text-muted fst-italic"> Not available</span>
              )}
            </div>
            {canEdit && (
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={() => setShowDateModal(true)}
                title="Edit date"
              >
                <i className="bi bi-pencil-fill"></i>
              </Button>
            )}
          </div>

          <div className="d-flex justify-content-between align-items-center mb-1">
            <div className="flex-grow-1">
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
            </div>
            {canEdit && (
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={() => setShowLocationModal(true)}
                title="Edit location"
              >
                <i className="bi bi-pencil-fill"></i>
              </Button>
            )}
          </div>

          <div className="d-flex justify-content-between align-items-center mb-1">
            <div>
              <strong>Folder: </strong>
              <Nav.Link as={Link} to={`/folders/${metadata.folder.id}`}>
                <i className="bi bi-folder-fill"></i>{" "}
                <span className="text-muted"> {metadata.folder.name}</span>
              </Nav.Link>
            </div>
          </div>

          {/* Permissions Section */}
          <div className="mb-3">
            <hr />
            <h6>Permissions</h6>
            <div className="mb-2">
              <small className="text-muted">View Groups:</small>
              <div>
                {metadata.view_groups ? (
                  metadata.view_groups.map((group) => (
                    <Badge key={group.id} bg="info" className="me-1 mb-1">
                      {group.name}
                    </Badge>
                  ))
                ) : (
                  <small className="text-muted">Unknown view groups</small>
                )}
              </div>
            </div>
            <div>
              <small className="text-muted">Edit Groups:</small>
              <div>
                {metadata.edit_groups ? (
                  metadata.edit_groups.map((group) => (
                    <Badge key={group.id} bg="warning" className="me-1 mb-1">
                      {group.name}
                    </Badge>
                  ))
                ) : (
                  <small className="text-muted">Unknown edit groups</small>
                )}
              </div>
            </div>
          </div>

          <hr />

          <p className="small mb-1">
            <strong>Created:</strong>
            <span className="text-muted"> {formatDate(profile, metadata.created_at)}</span>
          </p>

          <p className="small mb-1">
            <strong>Updated:</strong>
            <span className="text-muted"> {formatDate(profile, metadata.updated_at)}</span>
          </p>

          {/* Edit Permissions Button for Admins */}
          {canEdit && (
            <div className="d-grid gap-2 mt-3">
              <Button
                variant="outline-secondary"
                size="sm"
                onClick={() => setShowPermissionsModal(true)}
              >
                <i className="bi bi-shield-lock"></i> Edit Permissions
              </Button>
            </div>
          )}
        </Card.Body>
      </Card>
    </>
  );
};

export default ImageBasicInfoCard;
