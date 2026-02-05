import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Alert, Badge, Card, Col, Container, Row, Spinner } from "react-bootstrap";

import { getSystemStatisticsOptions } from "../api/@tanstack/react-query.gen";

const StatisticsDisplay: React.FC = () => {
  const { data: statistics, isLoading, isError, error } = useQuery(getSystemStatisticsOptions());

  if (isLoading) {
    return (
      <Container className="text-center py-3">
        <Spinner animation="border" size="sm" className="me-2" />
        <span>Loading statistics...</span>
      </Container>
    );
  }

  if (isError) {
    return (
      <Container className="py-3">
        <Alert variant="danger" className="py-2 mb-0">
          <strong>Error:</strong> {error?.message || "Failed to load statistics"}
        </Alert>
      </Container>
    );
  }

  if (!statistics) {
    return (
      <Container className="py-3">
        <Alert variant="info" className="py-2 mb-0">
          No statistics available
        </Alert>
      </Container>
    );
  }

  const { user_statistics, system_statistics } = statistics;

  const StatItem = ({
    label,
    value,
    variant = "primary",
  }: {
    label: string;
    value: number | string;
    variant?: string;
  }) => (
    <div className="d-flex justify-content-between align-items-center py-1 border-bottom border-light">
      <span className="text-muted small">{label}:</span>
      <Badge bg={variant} className="ms-2">
        {value}
      </Badge>
    </div>
  );

  return (
    <Container className="py-3">
      <div className="d-flex align-items-center mb-3">
        <h4 className="mb-0 text-dark fw-bold">System Statistics</h4>
      </div>

      <Row className="g-3">
        {/* User Statistics - Permissions & Counts */}
        <Col xl={8} lg={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-primary text-white py-2 px-3">
              <h6 className="mb-0 fw-semibold">Your Permissions & Counts</h6>
            </Card.Header>
            <Card.Body className="p-3">
              <Row>
                <Col md={6}>
                  <StatItem
                    label="Images Viewable"
                    value={user_statistics.total_images_viewable}
                  />
                  <StatItem
                    label="Images Editable"
                    value={user_statistics.total_images_editable}
                    variant="success"
                  />
                  <StatItem
                    label="Albums Viewable"
                    value={user_statistics.total_albums_viewable}
                  />
                  <StatItem
                    label="Albums Editable"
                    value={user_statistics.total_albums_editable}
                    variant="success"
                  />
                  <StatItem label="Tags" value={user_statistics.total_tags} variant="info" />
                  <StatItem
                    label="People Viewable"
                    value={user_statistics.total_people_viewable}
                  />
                  <StatItem
                    label="People Editable"
                    value={user_statistics.total_people_editable}
                    variant="success"
                  />
                </Col>
                <Col md={6}>
                  <StatItem label="Pets Viewable" value={user_statistics.total_pets_viewable} />
                  <StatItem
                    label="Pets Editable"
                    value={user_statistics.total_pets_editable}
                    variant="success"
                  />
                  <StatItem
                    label="Folders Viewable"
                    value={user_statistics.total_folders_viewable}
                  />
                  <StatItem
                    label="Folders Editable"
                    value={user_statistics.total_folders_editable}
                    variant="success"
                  />
                  <StatItem
                    label="Sources Viewable"
                    value={user_statistics.total_sources_viewable}
                  />
                  <StatItem
                    label="Sources Editable"
                    value={user_statistics.total_sources_editable}
                    variant="success"
                  />
                  <StatItem
                    label="Rough Dates"
                    value={user_statistics.total_rough_dates}
                    variant="info"
                  />
                  <StatItem
                    label="Rough Locations"
                    value={user_statistics.total_rough_locations}
                    variant="info"
                  />
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>

        {/* System Statistics - Disk Usage */}
        <Col xl={4} lg={12}>
          <Card className="border-0 shadow-sm">
            <Card.Header className="bg-secondary text-white py-2 px-3">
              <h6 className="mb-0 fw-semibold">System Resources</h6>
            </Card.Header>
            <Card.Body className="p-3">
              <Row className="align-items-center">
                <Col lg={4} xl={12} className="text-center mb-lg-0 mb-xl-3 mb-3">
                  <div className="display-6 fw-bold text-primary mb-1">
                    {(
                      ((system_statistics.disk_used_space_gb || 0) /
                        (system_statistics.disk_total_space_gb || 1)) *
                      100
                    ).toFixed(1)}
                    %
                  </div>
                  <small className="text-muted">Disk Usage</small>
                </Col>
                <Col lg={8} xl={12}>
                  <div className="progress mb-3" style={{ height: "8px" }}>
                    <div
                      className="progress-bar bg-gradient"
                      style={{
                        width: `${((system_statistics.disk_used_space_gb || 0) / (system_statistics.disk_total_space_gb || 1)) * 100}%`,
                        background:
                          "linear-gradient(90deg, #28a745 0%, #ffc107 70%, #dc3545 100%)",
                      }}
                    ></div>
                  </div>

                  <div className="small">
                    <StatItem
                      label="Total Space"
                      value={`${system_statistics.disk_total_space_gb?.toFixed(1) || "N/A"} GB`}
                      variant="info"
                    />
                    <StatItem
                      label="Used Space"
                      value={`${system_statistics.disk_used_space_gb?.toFixed(1) || "N/A"} GB`}
                      variant="warning"
                    />
                    <StatItem
                      label="Free Space"
                      value={`${system_statistics.disk_free_space_gb?.toFixed(1) || "N/A"} GB`}
                      variant="success"
                    />
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default StatisticsDisplay;
