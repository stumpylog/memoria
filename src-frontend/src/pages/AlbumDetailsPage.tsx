// src/pages/AlbumDetailsPage.tsx
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";

import {
  closestCenter,
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  rectSortingStrategy,
  SortableContext,
  sortableKeyboardCoordinates,
} from "@dnd-kit/sortable";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Row, Spinner } from "react-bootstrap";
import { useNavigate, useParams } from "react-router-dom";

import type {
  AlbumUpdateInSchema,
  AlbumWithImagesOutSchema,
  ImageThumbnailSchemaOut,
} from "../api";

import {
  getSingleAlbumInfo,
  imageGetThumbnailsBulkInfo,
  updateAlbumInfo,
  updateAlbumSorting,
} from "../api";
import EditAlbumInfoModal from "../components/album/EditAlbumInfoModal"; // This modal now handles groups too
import SortableImageListItem from "../components/album/SortableImageListItem";
import { useAuth } from "../hooks/useAuth";

const AlbumDetailsPage: React.FC = () => {
  const { albumId: albumIdParam } = useParams<{ albumId: string }>();
  const albumId = parseInt(albumIdParam || "0", 10);
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [displayedImages, setDisplayedImages] = useState<ImageThumbnailSchemaOut[]>([]);
  const [showEditInfoModal, setShowEditInfoModal] = useState(false); // Renamed for clarity
  const [editError, setEditError] = useState<string | null>(null);
  const [sortError, setSortError] = useState<string | null>(null);
  const [isSortDirty, setIsSortDirty] = useState<boolean>(false);
  const [activeId, setActiveId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const {
    data: album,
    isLoading: isLoadingAlbum,
    error: albumError,
  } = useQuery<AlbumWithImagesOutSchema | null, Error>({
    queryKey: ["albumDetails", albumId],
    queryFn: async (): Promise<AlbumWithImagesOutSchema | null> => {
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

  const { data: imageThumbnails, isLoading: isLoadingThumbnails } = useQuery({
    queryKey: ["albumImageThumbnails", albumId, album?.image_ids],
    queryFn: async (): Promise<ImageThumbnailSchemaOut[]> => {
      if (!album || !album.image_ids || album.image_ids.length === 0) return [];

      const response = await imageGetThumbnailsBulkInfo({ body: album.image_ids });
      const thumbnails = response.data || [];

      // Maintain the original order from album.image_ids
      const orderedResults: ImageThumbnailSchemaOut[] = [];
      const resultMap = new Map(thumbnails.map((thumb) => [thumb.id, thumb]));
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
      setIsSortDirty(false);
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
      setShowEditInfoModal(false);
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
      setIsSortDirty(false);
    },
    onError: (error: Error) => {
      setSortError(error.message || "Failed to save image order.");
      if (imageThumbnails) setDisplayedImages(imageThumbnails);
      setIsSortDirty(false);
    },
  });

  const handleSaveAlbumInfo = async (id: number, data: AlbumUpdateInSchema) => {
    await updateAlbumInfoMutation.mutateAsync({ albumIdToUpdate: id, data });
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id.toString());
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setDisplayedImages((images) => {
        const oldIndex = images.findIndex((img) => img.id.toString() === active.id);
        const newIndex = images.findIndex((img) => img.id.toString() === over.id);

        const newImages = arrayMove(images, oldIndex, newIndex);
        setIsSortDirty(true);
        return newImages;
      });
    }

    setActiveId(null);
  };

  const handleSaveChanges = () => {
    const newImageIds = displayedImages.map((img) => img.id);
    updateSortMutation.mutate(newImageIds);
  };

  const canEditAlbum = user?.is_staff || user?.is_superuser || false;

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

  const activeImage = activeId
    ? displayedImages.find((img) => img.id.toString() === activeId)
    : null;

  return (
    <Container fluid className="py-4">
      <title>Memoria Album: {album.name}</title>
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
              onClick={() => setShowEditInfoModal(true)} // Use the state for the single modal
              className="me-2"
            >
              Edit Album Info & Groups
            </Button>
          )}
          {canEditAlbum && (
            <Button
              variant="primary"
              onClick={handleSaveChanges}
              disabled={!isSortDirty || updateSortMutation.isPending}
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
      )}
      <Card>
        <Card.Header>Images</Card.Header>
        <Card.Body>
          <p className="text-muted small">Drag and drop images to reorder them.</p>
          {displayedImages.length > 0 ? (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={displayedImages.map((img) => img.id.toString())}
                strategy={rectSortingStrategy}
              >
                <Row>
                  {columnIndexes.map((colIdx) => (
                    <Col key={colIdx} md={12 / numColumns}>
                      {imagesByColumn[colIdx].map((image) => (
                        <SortableImageListItem
                          key={image.id}
                          image={image}
                          isDragging={activeId === image.id.toString()}
                          onViewClick={(id) => {
                            navigate(`/images/${id}`);
                          }}
                        />
                      ))}
                    </Col>
                  ))}
                </Row>
              </SortableContext>
              <DragOverlay>
                {activeImage ? (
                  <div
                    style={{
                      opacity: 0.8,
                      transform: "rotate(1deg)",
                      border: "2px solid #007bff",
                      borderRadius: "4px",
                    }}
                  >
                    <SortableImageListItem image={activeImage} isDragging={false} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          ) : (
            <Alert variant="info">This album is empty.</Alert>
          )}
        </Card.Body>
      </Card>
      {showEditInfoModal && canEditAlbum && (
        <EditAlbumInfoModal
          show={showEditInfoModal}
          onHide={() => {
            setShowEditInfoModal(false);
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
