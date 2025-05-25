import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Row, Spinner } from "react-bootstrap";
import { Helmet } from "react-helmet-async";
import { useParams } from "react-router-dom";

import type {
  AlbumUpdateInSchema,
  AlbumWithImagesReadInSchema,
  ImageThumbnailSchemaOut,
} from "../api";

import {
  getSingleAlbumInfo,
  imageGetThumbInfo,
  updateAlbumInfo,
  updateAlbumSorting,
} from "../api";
import EditAlbumInfoModal from "../components/album/EditAlbumInfoModal";
import SortableImageListItem from "../components/album/SortableImageListItem";
import { useAuth } from "../hooks/useAuth";

const AlbumDetailsPage: React.FC = () => {
  const { albumId: albumIdParam } = useParams<{ albumId: string }>();
  const albumId = parseInt(albumIdParam || "0", 10);
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [displayedImages, setDisplayedImages] = useState<ImageThumbnailSchemaOut[]>([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [sortError, setSortError] = useState<string | null>(null);
  const [isSortDirty, setIsSortDirty] = useState<boolean>(false); // New state to track sort changes

  const [draggedImageId, setDraggedImageId] = useState<number | null>(null);

  const {
    data: album,
    isLoading: isLoadingAlbum,
    error: albumError,
  } = useQuery<AlbumWithImagesReadInSchema | null, Error>({
    queryKey: ["albumDetails", albumId],
    queryFn: async (): Promise<AlbumWithImagesReadInSchema | null> => {
      if (!albumId || isNaN(albumId)) return null;
      try {
        const response = await getSingleAlbumInfo({ path: { album_id: albumId } });
        return response.data || null;
      } catch (error) {
        if (error instanceof Error && error.message.includes("404")) {
          return null;
        }
        throw error;
      }
    },
    enabled: !!albumId && !isNaN(albumId),
  });

  const { data: imageThumbnails, isLoading: isLoadingThumbnails } = useQuery<
    ImageThumbnailSchemaOut[],
    Error
  >({
    // Added Error type
    queryKey: ["albumImageThumbnails", albumId, album?.image_ids],
    queryFn: async (): Promise<ImageThumbnailSchemaOut[]> => {
      if (!album || !album.image_ids || album.image_ids.length === 0) return [];
      const thumbnailPromises = album.image_ids.map((id) =>
        imageGetThumbInfo({ path: { image_id: id } })
          .then((res) => res.data)
          .catch((err) => {
            console.error(`Failed to fetch thumbnail for image ${id}:`, err);
            return null;
          }),
      );
      const results = await Promise.all(thumbnailPromises);
      const orderedResults: ImageThumbnailSchemaOut[] = [];
      const resultMap = new Map(results.filter((r) => r !== null).map((r) => [r!.id, r!]));
      album.image_ids.forEach((id) => {
        const thumb = resultMap.get(id);
        if (thumb) {
          orderedResults.push(thumb);
        }
      });
      return orderedResults;
    },
    enabled: !!album && !!album.image_ids && album.image_ids.length > 0,
  });

  useEffect(() => {
    if (imageThumbnails) {
      setDisplayedImages(imageThumbnails);
      setIsSortDirty(false); // Reset dirty state when original thumbnails load or change
    }
  }, [imageThumbnails]);

  const updateAlbumInfoMutation = useMutation({
    mutationFn: ({
      albumIdToUpdate,
      data,
    }: {
      albumIdToUpdate: number;
      data: AlbumUpdateInSchema;
    }) => updateAlbumInfo({ path: { album_id: albumIdToUpdate }, body: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albumDetails", albumId] });
      queryClient.invalidateQueries({ queryKey: ["albums"] });
      setShowEditModal(false);
      setEditError(null);
    },
    onError: (error: Error) => {
      setEditError(error.message || "Failed to update album information.");
    },
  });

  const updateSortMutation = useMutation({
    mutationFn: (newSortOrder: number[]) =>
      updateAlbumSorting({ path: { album_id: albumId }, body: { sorting: newSortOrder } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albumDetails", albumId] });
      setSortError(null);
      setIsSortDirty(false); // Sort changes saved, reset dirty state
    },
    onError: (error: Error) => {
      setSortError(error.message || "Failed to save image order.");
      if (imageThumbnails) setDisplayedImages(imageThumbnails); // Revert on error
      setIsSortDirty(false); // Revert dirty state on error
    },
  });

  const handleSaveAlbumInfo = async (id: number, data: AlbumUpdateInSchema) => {
    await updateAlbumInfoMutation.mutateAsync({ albumIdToUpdate: id, data });
  };

  const handleDragStart = (event: React.DragEvent<HTMLDivElement>, imageId: number) => {
    setDraggedImageId(imageId);
    event.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>, targetImageId: number) => {
    event.preventDefault();
    if (draggedImageId === null || draggedImageId === targetImageId) {
      return;
    }

    const newImages = [...displayedImages];
    const draggedItemIndex = newImages.findIndex((img) => img.id === draggedImageId);
    const targetItemIndex = newImages.findIndex((img) => img.id === targetImageId);

    if (draggedItemIndex === -1 || targetItemIndex === -1) return;

    const [draggedItem] = newImages.splice(draggedItemIndex, 1);
    newImages.splice(targetItemIndex, 0, draggedItem);

    setDisplayedImages(newImages);
    setIsSortDirty(true); // User has reordered, set dirty state
  };

  const handleDragEnd = () => {
    setDraggedImageId(null);
  };

  const handleSaveChanges = () => {
    const newImageIds = displayedImages.map((img) => img.id);
    updateSortMutation.mutate(newImageIds);
  };

  const canEditAlbum = user?.is_staff || user?.is_superuser || false; // Simplified permission check

  if (
    isLoadingAlbum ||
    (album && album.image_ids && album.image_ids.length > 0 && isLoadingThumbnails)
  ) {
    return (
      <Container className="text-center mt-5">
        <Spinner animation="border" />
        <p>Loading album details...</p>
      </Container>
    );
  }

  if (albumError) {
    return (
      <Container className="mt-5">
        <Alert variant="danger">
          {albumError instanceof Error ? albumError.message : "Failed to load album."}
        </Alert>
      </Container>
    );
  }

  if (!album) {
    return (
      <Container className="mt-5">
        <Alert variant="warning">Album not found.</Alert>
      </Container>
    );
  }

  const numColumns = 4;
  const columnIndexes = Array.from(Array(numColumns).keys());
  const imagesByColumn = columnIndexes.map((colIndex) =>
    displayedImages.filter((_, imgIndex) => imgIndex % numColumns === colIndex),
  );

  return (
    <Container fluid className="py-4">
      <Helmet>
        <title>Album: {album.name}</title>
      </Helmet>
      <Row className="mb-3 align-items-center">
        <Col>
          <h1>{album.name}</h1>
          <p className="text-muted">{album.description || "No description."}</p>
          <p>Contains {album.image_count} image(s).</p>
        </Col>
        <Col xs="auto">
          {canEditAlbum && (
            <Button
              variant="outline-primary"
              onClick={() => setShowEditModal(true)}
              className="me-2"
            >
              Edit Album Info
            </Button>
          )}
          {canEditAlbum && (
            <Button
              variant="primary"
              onClick={handleSaveChanges}
              disabled={!isSortDirty || updateSortMutation.isPending} // Enable only when dirty and not saving
            >
              {updateSortMutation.isPending ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                  />
                  {" Saving Order..."}
                </>
              ) : (
                "Save Sort Order"
              )}
            </Button>
          )}
        </Col>
      </Row>
      {sortError && (
        <Alert variant="danger" onClose={() => setSortError(null)} dismissible>
          Failed to save image order: {sortError}
        </Alert>
      )}
      {updateSortMutation.isPending && !sortError && (
        <div className="text-center my-2">
          <Spinner size="sm" /> Saving new order...
        </div>
      )}{" "}
      {/* Only show saving message if no error */}
      <Card>
        <Card.Header>Images</Card.Header>
        <Card.Body>
          <p className="text-muted small">Drag and drop images to reorder them.</p>
          {displayedImages.length > 0 ? (
            <Row>
              {columnIndexes.map((colIdx) => (
                <Col key={colIdx} md={12 / numColumns}>
                  {imagesByColumn[colIdx].map((image) => (
                    <SortableImageListItem
                      key={image.id}
                      image={image}
                      onDragStart={handleDragStart}
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                      onDragEnd={handleDragEnd}
                      isDragging={draggedImageId === image.id}
                    />
                  ))}
                </Col>
              ))}
            </Row>
          ) : (
            <Alert variant="info">This album is empty.</Alert>
          )}
        </Card.Body>
      </Card>
      {showEditModal && canEditAlbum && (
        <EditAlbumInfoModal
          show={showEditModal}
          onHide={() => {
            setShowEditModal(false);
            setEditError(null);
          }}
          album={album}
          onSave={handleSaveAlbumInfo}
          isLoading={updateAlbumInfoMutation.isPending}
          error={editError}
        />
      )}
    </Container>
  );
};

export default AlbumDetailsPage;
