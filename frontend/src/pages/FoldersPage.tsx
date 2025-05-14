import React, { useEffect, useState } from 'react';
import { Container, Spinner, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import FolderWall from '../components/folder/FolderWall';
import type { RootFolderSchema } from '../api';
import { folderListRoots } from '../api';
import { Helmet } from 'react-helmet-async';

interface FoldersPageProps {
  onFolderClick?: (id: number) => void;
  buttonText?: string;
  truncateDescription?: number;
}

const FoldersPage: React.FC<FoldersPageProps> = ({
  onFolderClick,
  buttonText = "View Folder",
  truncateDescription = 100
}) => {
  const [folders, setFolders] = useState<RootFolderSchema[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchFolders = async () => {
      try {
        setLoading(true);
        const response = await folderListRoots();
        setFolders(response.data || []);
        setError(null);
      } catch (err) {
        setError('Failed to load folders. Please try again later.');
        console.error('Error fetching folders:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFolders();
  }, []);

  const handleFolderClick = (id: number) => {
    if (onFolderClick) {
      onFolderClick(id);
    } else {
      // Use react-router navigation
      navigate(`/folders/${id}`);
    }
  };

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  if (folders.length === 0) {
    return (
      <Container>
        <Alert variant="info">No folders available.</Alert>
      </Container>
    );
  }

  return (
    <Container fluid>
      <Helmet>
              <title>Memoria - All Folders</title>
            </Helmet>
      <h2 className="mb-4">Folders</h2>
      <FolderWall
        folders={folders}
        buttonText={buttonText}
        truncateDescription={truncateDescription}
        onFolderClick={handleFolderClick}
      />
    </Container>
  );
};

export default FoldersPage;
