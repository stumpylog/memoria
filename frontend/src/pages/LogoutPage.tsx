// src/pages/LogoutPage.tsx
import { Container, Card } from 'react-bootstrap';
import LinkButton from '../components/common/LinkButton';

const LogoutPage: React.FC = () => {
  return (
    <Container className="d-flex align-items-center justify-content-center" style={{ minHeight: '80vh' }}>
      <Card style={{ width: '100%', maxWidth: '500px' }} className="text-center">
        <Card.Body>
          <Card.Title>You have been logged out</Card.Title>
          <Card.Text>
            Thank you for using our application. You can log back in at any time.
          </Card.Text>
          <LinkButton to="/login" variant="primary">
            Log Back In
          </LinkButton>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default LogoutPage;
