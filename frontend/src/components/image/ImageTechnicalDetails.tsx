// src/components/image/ImageTechnicalDetails.tsx

import React from "react";
import { Card, Col, Row } from "react-bootstrap";

import type { ImageMetadataSchema } from "../../api";

import { formatBytes } from "../../utils/formatBytes";

interface ImageTechnicalDetailsProps {
  metadata: ImageMetadataSchema;
}

const getOrientationDisplay = (orientation: number | null | undefined): string => {
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
};

const ImageTechnicalDetails: React.FC<ImageTechnicalDetailsProps> = ({ metadata }) => {
  return (
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
  );
};

export default ImageTechnicalDetails;
