import React from "react";
import { Button, Card } from "react-bootstrap";

import type { RootFolderSchema } from "../../api";

interface FolderCardProps {
  folder: RootFolderSchema;
  buttonText?: string;
  truncateDescription?: number;
  onButtonClick?: (id: number) => void;
}

const FolderCard: React.FC<FolderCardProps> = ({
  folder,
  buttonText = "View",
  truncateDescription,
  onButtonClick,
}) => {
  const childCount = folder.child_count || 0;
  const imageCount = folder.image_count || 0;

  const handleButtonClick = () => {
    if (onButtonClick) {
      onButtonClick(folder.id);
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + "...";
  };

  return (
    <div className="col-md-4 mb-4">
      <Card>
        <Card.Body>
          <h5 className="card-title">{folder.name}</h5>

          {folder.description && (
            <p className="card-text">
              {truncateDescription
                ? truncateText(folder.description, truncateDescription)
                : folder.description}
            </p>
          )}

          <p className="card-text">Contains {childCount} folder(s)</p>
          <p className="card-text">Contains {imageCount} image(s)</p>

          <Button variant="primary" onClick={handleButtonClick}>
            {buttonText}
          </Button>
        </Card.Body>
      </Card>
    </div>
  );
};

export default FolderCard;
