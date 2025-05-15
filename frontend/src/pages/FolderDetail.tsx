import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Container, Breadcrumb, Spinner, Alert } from "react-bootstrap";
import { useQuery } from "@tanstack/react-query";
import FolderWall from "../components/folder/FolderWall";
import ImageWall from "../components/image/ImageWall";
import { folderGetDetails, imageGetThumbInfo } from "../api";
import type { FolderDetailSchema, ImageThumbnailSchema } from "../api";
import { Helmet } from "react-helmet-async";

interface FolderDetailProps {}

const FolderDetail: React.FC<FolderDetailProps> = () => {
  const { id } = useParams<{ id: string }>();
  const folderId = parseInt(id || "0", 10);
  const navigate = useNavigate();

  // Query for folder details
  const {
    data: folderDetail,
    isLoading: folderLoading,
    error: folderError,
  } = useQuery({
    queryKey: ["folder", folderId],
    queryFn: async (): Promise<FolderDetailSchema> => {
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
    queryFn: async (): Promise<ImageThumbnailSchema[]> => {
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
      return results.filter((item): item is ImageThumbnailSchema => item !== null);
    },
    enabled: !!folderDetail && folderDetail.folder_images?.length > 0,
  });

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
      <Helmet>
        <title>Memoria - Folder: {folderDetail.name}</title>
      </Helmet>

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
        <h2 className="mb-3">Images ({folderDetail.folder_images.length})</h2>

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
          <ImageWall
            images={imageThumbs}
            onImageClick={(imageId) => {
              navigate(`/images/${imageId}`);
            }}
            columns={4}
          />
        ) : (
          <Alert variant="info">This folder contains no images.</Alert>
        )}
      </>
    </Container>
  );
};

export default FolderDetail;
