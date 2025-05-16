// src/components/image/ImageBasicInfoCard.tsx

import React from "react";
import { Card } from "react-bootstrap";

import type {
  ImageDateSchema,
  ImageLocationSchema,
  ImageMetadataSchema,
  UserProfileOutSchema,
} from "../../api";

interface ImageBasicInfoCardProps {
  metadata: ImageMetadataSchema;
  location: ImageLocationSchema | null;
  dateInfo: ImageDateSchema | null;
  profile: UserProfileOutSchema | null;
}

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

const ImageBasicInfoCard: React.FC<ImageBasicInfoCardProps> = ({
  metadata,
  location,
  dateInfo,
  profile,
}) => {
  return (
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
  );
};

export default ImageBasicInfoCard;
