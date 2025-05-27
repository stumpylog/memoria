import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Alert, Breadcrumb, Button, Container, Spinner } from "react-bootstrap";
import { Link, useNavigate, useParams } from "react-router-dom";

import type { AlbumAddImageInSchema } from "../api";
import type { FolderDetailSchemaOut, ImageThumbnailSchemaOut } from "../api";

import { folderGetDetails, imageGetThumbInfo } from "../api";
import { addImageToAlbum } from "../api";
import EditFolderModal from "../components/folder/EditFolderModal";
import FolderWall from "../components/folder/FolderWall";
import AddToAlbumModal from "../components/image/AddToAlbumModal";
import SelectableImageWall from "../components/image/SelectableImageWall";
import { useAuth } from "../hooks/useAuth";
import { formatDate } from "../utils/formatDate";
import { getGridColumns } from "../utils/getGridColums";

interface FolderDetailProps {}

const FolderDetail: React.FC<FolderDetailProps> = () => {
  const { id } = useParams<{ id: string }>();
  const { profile } = useAuth();
  const folderId = parseInt(id || "0", 10);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedImageIds, setSelectedImageIds] = useState<number[]>([]);
  const [showAlbumModal, setShowAlbumModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false); // New state for edit modal

  const handleShowEditModal = () => setShowEditModal(true); // New handler
  const handleCloseEditModal = () => setShowEditModal(false); // New handler

  // Query for folder details
  const {
    data: folderDetail,
    isLoading: folderLoading,
    error: folderError,
    refetch: refetchFolder, // Add refetch
  } = useQuery({
    queryKey: ["folder", folderId],
    queryFn: async (): Promise<FolderDetailSchemaOut> => {
      if (!folderId) {
        throw new Error("Invalid folder ID.");
      }
      const response = await folderGetDetails({
        path: { folder_id: folderId },
      });
      if (!response.data) {
        throw new Error("Folder not found.");
      }
      return response.data;
    },
    enabled: !!folderId && folderId > 0,
  });

  // Dependent query for image thumbnails
  const {
    data: imageThumbs = [],
    isLoading: imagesLoading,
    error: imagesError,
  } = useQuery({
    queryKey: ["folderImages", folderId],
    queryFn: async (): Promise<ImageThumbnailSchemaOut[]> => {
      if (!folderDetail?.folder_images?.length) {
        return [];
      }

      const thumbInfoPromises = folderDetail.folder_images.map((imageId) =>
        imageGetThumbInfo({ path: { image_id: imageId } })
          .then((response) => response.data)
          .catch((err) => {
            console.error(`Error fetching thumbnail info for image ID ${imageId}:`, err);
            return null;
          }),
      );

      const results = await Promise.all(thumbInfoPromises);
      return results.filter((item): item is ImageThumbnailSchemaOut => item !== null);
    },
    enabled: !!folderDetail && folderDetail.folder_images?.length > 0,
  });

  // Add to Album Mutation
  const addToAlbumMutation = useMutation({
    mutationFn: async ({ albumId, imageIds }: { albumId: number; imageIds: number[] }) => {
      const updatedData: AlbumAddImageInSchema = { image_ids: imageIds };
      return await addImageToAlbum({ path: { album_id: albumId }, body: updatedData });
    },
    onSuccess: () => {
      setSelectedImageIds([]);
      setShowAlbumModal(false);
      queryClient.invalidateQueries({ queryKey: ["albums"] });
    },
    onError: (error) => {
      console.error("Failed to add images to album:", error);
    },
  });

  // Handle successful save from EditFolderModal
  const handleSaveSuccess = () => {
    refetchFolder(); // Refetch folder details after a successful edit
    queryClient.invalidateQueries({ queryKey: ["folderImages"] }); // Invalidate images too as permissions might change
  };

  const handleSelectionChange = (newSelectedIds: number[]) => {
    setSelectedImageIds(newSelectedIds);
  };

  const handleOpenAlbumModal = () => {
    if (selectedImageIds.length > 0) {
      setShowAlbumModal(true);
    }
  };

  const handleAddToAlbum = async (albumId: number, imageIds: number[]) => {
    addToAlbumMutation.mutate({ albumId, imageIds });
  };

  if (folderLoading) {
    return (
      <Container
        className="d-flex justify-content-center align-items-center"
        style={{ minHeight: "200px" }}
      >
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading folder details...</span>
        </Spinner>
      </Container>
    );
  }

  if (folderError || !folderDetail) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">
          {folderError instanceof Error
            ? folderError.message
            : "Folder not found or an unexpected error occurred."}
        </Alert>
      </Container>
    );
  }

  // Calculate if there are any missing images
  const missingImagesCount = folderDetail.folder_images.length - imageThumbs.length;
  const hasImageLoadError = imagesError || (missingImagesCount > 0 && !imagesLoading);

  return (
    <Container fluid>
      <title>Memoria - Folder: {folderDetail.name}</title>

      {/* Breadcrumb navigation */}
      <Breadcrumb className="mt-3 mb-4">
        <Breadcrumb.Item linkAs={Link} linkProps={{ to: "/folders" }}>
          Home
        </Breadcrumb.Item>
        {folderDetail.breadcrumbs.map((crumb, index) => (
          <Breadcrumb.Item
            key={crumb.id}
            linkAs={Link}
            linkProps={{ to: `/folders/${crumb.id}` }}
            active={index === folderDetail.breadcrumbs.length - 1}
          >
            {crumb.name}
          </Breadcrumb.Item>
        ))}
      </Breadcrumb>

      <h1 className="mb-4">Current Folder: {folderDetail.name}</h1>

      {/* Display description or "No description" */}
      {folderDetail.description ? (
        <p>{folderDetail.description}</p>
      ) : (
        <p className="text-muted font-italic">No description</p>
      )}

      {/* Display Created At and Updated At */}
      {folderDetail && (
        <div className="mb-3 text-muted small">
          <p className="mb-0">
            <strong>Created At:</strong> {formatDate(profile, folderDetail.created_at)}
          </p>
          <p className="mb-0">
            <strong>Updated At:</strong> {formatDate(profile, folderDetail.updated_at)}
          </p>
        </div>
      )}

      {/* Edit button */}
      {folderId && ( // Ensure folderId is available before rendering the button
        <Button onClick={handleShowEditModal} className="mb-3">
          Edit
        </Button>
      )}

      {/* Child Folders Section */}
      <>
        <h2 className="mb-3">Child Folders</h2>
        {folderDetail.child_folders.length > 0 ? (
          <FolderWall
            folders={folderDetail.child_folders}
            buttonText="Open"
            truncateDescription={100}
            onFolderClick={(childId) => {
              navigate(`/folders/${childId}`);
            }}
          />
        ) : (
          <Alert variant="info">This folder contains no child folders.</Alert>
        )}
      </>

      {/* Separator Line */}
      <hr className="my-5" />

      {/* Images Section */}
      <>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h2>Images ({folderDetail.folder_images.length})</h2>
          {selectedImageIds.length > 0 && (
            <Button
              variant="primary"
              onClick={handleOpenAlbumModal}
              disabled={addToAlbumMutation.isPending}
            >
              {addToAlbumMutation.isPending ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                  />
                  <span className="ms-2">Processing...</span>
                </>
              ) : (
                `Add ${selectedImageIds.length} selected to album`
              )}
            </Button>
          )}
        </div>

        {imagesLoading ? (
          <div className="d-flex justify-content-center align-items-center my-3">
            <Spinner animation="border" size="sm" role="status">
              <span className="visually-hidden">Loading images...</span>
            </Spinner>
            <span className="ms-2">Loading images...</span>
          </div>
        ) : hasImageLoadError ? (
          <Alert variant="warning">
            {missingImagesCount > 0
              ? `Failed to load thumbnail info for ${missingImagesCount} out of ${folderDetail.folder_images.length} images.`
              : "Failed to load image thumbnails."}
          </Alert>
        ) : imageThumbs.length > 0 ? (
          <SelectableImageWall
            images={imageThumbs}
            onImageClick={(imageId) => {
              navigate(`/images/${imageId}`);
            }}
            columns={getGridColumns(profile?.items_per_page || 30)}
            onSelectionChange={handleSelectionChange}
          />
        ) : (
          <Alert variant="info">This folder contains no images.</Alert>
        )}
      </>

      {/* Album Modal */}
      <AddToAlbumModal
        show={showAlbumModal}
        onHide={() => setShowAlbumModal(false)}
        selectedImageIds={selectedImageIds}
        onAddToAlbum={handleAddToAlbum}
        isLoading={addToAlbumMutation.isPending}
        isError={addToAlbumMutation.isError}
        error={addToAlbumMutation.error}
      />

      {/* Edit Folder Modal */}
      {folderDetail && (
        <EditFolderModal
          show={showEditModal}
          handleClose={handleCloseEditModal}
          folder={folderDetail}
          onSaveSuccess={handleSaveSuccess}
        />
      )}
    </Container>
  );
};

export default FolderDetail;
