// src/pages/ProfilePage.tsx
import React from 'react';
import { Container, Card } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();

  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">User Profile</Card.Header>
        <Card.Body>
          {user ? (
            <>
              <Card.Text><strong>Username:</strong> {user.username}</Card.Text>
              <Card.Text><strong>Email:</strong> {user.email}</Card.Text>
              <Card.Text><strong>First Name:</strong> {user.first_name}</Card.Text>
              <Card.Text><strong>Last Name:</strong> {user.last_name}</Card.Text>
              <Card.Text><strong>Timezone:</strong> {user.profile.timezone}</Card.Text>
              <Card.Text><strong>Default Items Per Page:</strong> {user.profile.default_items_per_page}</Card.Text>
              <Card.Text><em>More profile editing features can be added here.</em></Card.Text>
            </>
          ) : (
            <Card.Text>Loading profile...</Card.Text>
          )}
        </Card.Body>
      </Card>
    </Container>
  );
};

export default ProfilePage;
