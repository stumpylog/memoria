// src/pages/ProfilePage.tsx
import React from "react";
import { Card, Container } from "react-bootstrap";
import { Helmet } from "react-helmet-async";

import { useAuth } from "../hooks/useAuth";

const ProfilePage: React.FC = () => {
  const { user, profile } = useAuth();

  return (
    <Container fluid className="p-4">
      <Helmet>
        <title>Profile: {user?.username}</title>
      </Helmet>
      <Card>
        <Card.Header as="h2">User Profile</Card.Header>
        <Card.Body>
          {user ? (
            <>
              <Card.Text>
                <strong>Username:</strong> {user.username}
              </Card.Text>
              <Card.Text>
                <strong>Email:</strong> {user.email}
              </Card.Text>
              <Card.Text>
                <strong>First Name:</strong> {user.first_name}
              </Card.Text>
              <Card.Text>
                <strong>Last Name:</strong> {user.last_name}
              </Card.Text>
            </>
          ) : (
            <Card.Text>Loading user info...</Card.Text>
          )}
          {profile ? (
            <>
              <Card.Text>
                <strong>Timezone:</strong> {profile.timezone_name}
              </Card.Text>
              <Card.Text>
                <strong>Default Items Per Page:</strong> {profile.items_per_page}
              </Card.Text>
            </>
          ) : (
            <Card.Text>Loading user profile...</Card.Text>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ProfilePage;
