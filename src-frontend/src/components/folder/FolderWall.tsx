import React from "react";
import { Container, Row } from "react-bootstrap";

import type { RootFolderSchemaOut } from "../../api";

import FolderCard from "./FolderCard";

interface FolderWallProps {
  folders: RootFolderSchemaOut[];
  buttonText?: string;
  truncateDescription?: number;
  onFolderClick?: (id: number) => void;
}

const FolderWall: React.FC<FolderWallProps> = ({
  folders,
  buttonText,
  truncateDescription,
  onFolderClick,
}) => {
  return (
    <Container>
      <Row>
        {folders.map((folder) => (
          <FolderCard
            key={folder.id}
            folder={folder}
            buttonText={buttonText}
            truncateDescription={truncateDescription}
            onButtonClick={onFolderClick}
          />
        ))}
      </Row>
    </Container>
  );
};

export default FolderWall;
