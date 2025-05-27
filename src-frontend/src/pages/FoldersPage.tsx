import { useQuery } from "@tanstack/react-query";
import React from "react";
import { Alert, Container, Spinner } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

import type { RootFolderSchema } from "../api";

import { folderListRoots } from "../api";
import FolderWall from "../components/folder/FolderWall";

interface FoldersPageProps {
  onFolderClick?: (id: number) => void;
  buttonText?: string;
  truncateDescription?: number;
}

const FoldersPage: React.FC<FoldersPageProps> = ({
  onFolderClick,
  buttonText = "View Folder",
  truncateDescription = 100,
}) => {
  const navigate = useNavigate();

  const {
    data: folders = [],
    isLoading,
    error,
  } = useQuery<RootFolderSchema[]>({
    queryKey: ["folders", "roots"],
    queryFn: async () => {
      const response = await folderListRoots();
      return response.data || [];
    },
  });

  const handleFolderClick = (id: number) => {
    if (onFolderClick) {
      onFolderClick(id);
    } else {
      // Use react-router navigation
      navigate(`/folders/${id}`);
    }
  };

  if (isLoading) {
    return (
      <Container
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: "200px" }}
      >
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert variant="danger">Failed to load folders. Please try again later.</Alert>
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
      <title>Memoria - All Folders</title>
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
