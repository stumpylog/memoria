import { useQuery } from "@tanstack/react-query"; // Import useQuery from react-query
import React from "react";
import { Alert, Card, Col, Container, ListGroup, Row, Spinner } from "react-bootstrap";

import type { StatisticsResponseSchema } from "../api";

import { getSystemStatistics } from "../api";

const StatisticsDisplay: React.FC = () => {
  // Use react-query's useQuery hook for data fetching and state management
  const {
    data: statistics,
    isLoading,
    isError,
    error,
  } = useQuery<StatisticsResponseSchema, Error>({
    queryKey: ["systemStatistics"], // Unique key for this query
    queryFn: async () => {
      // Call the imported getSystemStatistics function
      const response = await getSystemStatistics();

      // Ensure that response.data is not undefined before returning.
      // If the API client's 'get' method can return undefined data on success,
      // we must explicitly handle it here by throwing an error, as react-query expects
      // the queryFn to either return the expected data type or throw an error.
      if (!response.data) {
        throw new Error("API did not return expected statistics data.");
      }
      return response.data;
    },
    // Optional: Add staleTime, cacheTime, refetchOnWindowFocus, etc. as needed
  });

  if (isLoading) {
    return (
      <Container className="text-center my-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading statistics...</span>
        </Spinner>
        <p className="mt-3">Loading statistics...</p>
      </Container>
    );
  }

  if (isError) {
    return (
      <Container className="my-5">
        <Alert variant="danger">
          <Alert.Heading>Oh snap! You got an error!</Alert.Heading>
          <p>Failed to load statistics: {error?.message || "An unknown error occurred"}</p>
          <hr />
          <p className="mb-0">
            Please try refreshing the page or contact support if the issue persists.
          </p>
        </Alert>
      </Container>
    );
  }

  if (!statistics) {
    return (
      <Container className="my-5">
        <Alert variant="info">No statistics data available.</Alert>
      </Container>
    );
  }

  const { user_statistics, system_statistics } = statistics;

  return (
    <Container className="my-5 p-4 rounded-lg shadow-lg bg-gray-50 font-inter">
      <h1 className="text-4xl font-bold text-center mb-6 text-gray-800">System Statistics</h1>

      {/* User Statistics Section */}
      <Row className="mb-6">
        <Col xs={12}>
          <Card className="shadow-md rounded-lg border-0">
            <Card.Header className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-xl font-semibold py-3 px-4 rounded-t-lg">
              Your Permissions & Counts
            </Card.Header>
            <Card.Body className="p-4">
              <Row>
                <Col md={6}>
                  <ListGroup variant="flush">
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Images Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_images_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Images Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_images_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Albums Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_albums_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Albums Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_albums_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Tags Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_tags_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Tags Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_tags_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      People Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_people_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      People Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_people_editable}
                      </span>
                    </ListGroup.Item>
                  </ListGroup>
                </Col>
                <Col md={6}>
                  <ListGroup variant="flush">
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Pets Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_pets_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Pets Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_pets_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Folders Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_folders_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Folders Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_folders_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Sources Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_sources_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Sources Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_sources_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Rough Dates Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_rough_dates_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Rough Dates Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_rough_dates_editable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Rough Locations Viewable:{" "}
                      <span className="badge bg-primary rounded-pill">
                        {user_statistics.total_rough_locations_viewable}
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                      Rough Locations Editable:{" "}
                      <span className="badge bg-success rounded-pill">
                        {user_statistics.total_rough_locations_editable}
                      </span>
                    </ListGroup.Item>
                  </ListGroup>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Statistics Section */}
      <Row>
        <Col xs={12}>
          <Card className="shadow-md rounded-lg border-0">
            <Card.Header className="bg-gradient-to-r from-purple-600 to-pink-500 text-white text-xl font-semibold py-3 px-4 rounded-t-lg">
              System Information
            </Card.Header>
            <Card.Body className="p-4">
              <ListGroup variant="flush">
                <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                  Disk Total Space (GB):{" "}
                  <span className="badge bg-info rounded-pill">
                    {system_statistics.disk_total_space_gb?.toFixed(2) || "N/A"}
                  </span>
                </ListGroup.Item>
                <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                  Disk Used Space (GB):{" "}
                  <span className="badge bg-warning rounded-pill">
                    {system_statistics.disk_used_space_gb?.toFixed(2) || "N/A"}
                  </span>
                </ListGroup.Item>
                <ListGroup.Item className="d-flex justify-content-between align-items-center bg-transparent border-0 py-2 px-0">
                  Disk Free Space (GB):{" "}
                  <span className="badge bg-success rounded-pill">
                    {system_statistics.disk_free_space_gb?.toFixed(2) || "N/A"}
                  </span>
                </ListGroup.Item>
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default StatisticsDisplay;
