// src/pages/SettingsPage.tsx
import React from 'react';
import { Container, Card, Alert } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';


const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  // This check can also be part of ProtectedRoute if settings becomes a common protected resource type
  if (user && !user.is_staff && !user.is_superuser) {
    return <Navigate to="/" replace />; // Or to an "Unauthorized" page
  }

  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">Application Settings</Card.Header>
        <Card.Body>
          <Alert variant="info">This page is available to staff and superusers only.</Alert>
          <Card.Text>Application-wide settings will be managed here.</Card.Text>
          {/* Add settings controls here */}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default SettingsPage;
