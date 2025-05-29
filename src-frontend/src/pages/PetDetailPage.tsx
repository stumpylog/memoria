// src/pages/PetDetailsPage.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import { Alert, Button, Col, Container, Row, Spinner } from "react-bootstrap";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import type {
  ImagesPerPageChoices,
  ImageThumbnailSchemaOut,
  PetImageOutSchema,
  PetReadDetailSchemaOut,
} from "../api";

import { addImageToAlbum, getPetDetail, getPetImages, imageGetThumbnailsBulkInfo } from "../api";
import AddToAlbumModal from "../components/image/AddToAlbumModal";
import SelectableImageWall from "../components/image/SelectableImageWall";
import EditPetModal from "../components/pets/EditPetModal";
import { useAuth } from "../hooks/useAuth";
import { formatDate } from "../utils/formatDate";
import { getGridColumns } from "../utils/getGridColums";

const PetDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { profile } = useAuth();

  const petId = id ? parseInt(id, 10) : undefined;
  const isValidId = petId !== undefined && !isNaN(petId);

  const [searchParams, setSearchParams] = useSearchParams();
  const [limit, setLimit] = useState<number>(profile?.items_per_page || 30);
  const offset = parseInt(searchParams.get("offset") || "0", 10);

  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedImageIds, setSelectedImageIds] = useState<number[]>([]);
  const [showAlbumModal, setShowAlbumModal] = useState(false);
  const isInitialRender = useRef(true);

  useEffect(() => {
    const profileLimit = profile?.items_per_page || 30;
    const urlLimit = searchParams.get("limit")
      ? parseInt(searchParams.get("limit")!, 10)
      : undefined;

    if (profile && profileLimit !== limit) {
      setLimit(profileLimit);
    } else if (urlLimit && urlLimit !== limit) {
      setLimit(urlLimit);
    } else if (!urlLimit && profileLimit !== limit && isInitialRender.current) {
      setLimit(profileLimit);
    }

    if (!isInitialRender.current && profile && profileLimit !== urlLimit) {
      setSearchParams(
        (prev) => {
          const newParams = new URLSearchParams(prev);
          if (profileLimit !== 30) newParams.set("limit", profileLimit.toString());
          else newParams.delete("limit");
          return newParams;
        },
        { replace: true },
      );
    }

    isInitialRender.current = false;
  }, [profile, searchParams, setSearchParams, limit]);

  const {
    data: pet,
    isLoading: isLoadingPet,
    isError: isErrorPet,
    error: errorPet,
  } = useQuery<PetReadDetailSchemaOut | null>({
    queryKey: ["pet", petId],
    queryFn: async () => {
      if (!isValidId) throw new Error("Invalid pet ID.");
      const response = await getPetDetail({ path: { pet_id: petId! } });
      return response.data || null;
    },
    enabled: isValidId,
    staleTime: 5 * 60 * 1000,
  });

  const {
    data: pagedImageData,
    isLoading: isLoadingImageIds,
    isError: isErrorImageIds,
    error: errorImageIds,
  } = useQuery<PetImageOutSchema[]>({
    queryKey: ["pet-image-ids", petId, limit, offset],
    queryFn: async () => {
      if (!petId) throw new Error("Pet ID is undefined.");
      const response = await getPetImages({ path: { pet_id: petId }, query: { limit, offset } });
      return response.data?.items || [];
    },
    enabled: isValidId && !!pet,
    staleTime: 5 * 60 * 1000,
  });

  const imageIds = pagedImageData?.map((img) => img.id) || [];

  const {
    data: images,
    isLoading: isLoadingImages,
    isError: isErrorImages,
    error: errorImages,
  } = useQuery<ImageThumbnailSchemaOut[] | null>({
    queryKey: ["pet-images-thumbnails", imageIds.join(",")],
    queryFn: async () => {
      if (imageIds.length === 0) return [];
      const response = await imageGetThumbnailsBulkInfo({ body: imageIds });
      return response.data || [];
    },
    enabled: imageIds.length > 0,
    staleTime: 5 * 60 * 1000,
  });

  const totalImageCount = pet?.image_count || 0;
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = totalImageCount ? Math.ceil(totalImageCount / limit) : 0;

  const addToAlbumMutation = useMutation({
    mutationFn: ({ albumId, imageIds }: { albumId: number; imageIds: number[] }) =>
      addImageToAlbum({ path: { album_id: albumId }, body: { image_ids: imageIds } }),
    onSuccess: () => {
      setSelectedImageIds([]);
      setShowAlbumModal(false);
    },
    onError: (error) => console.error("Failed to add images to album:", error),
  });

  const handleNextPage = () => {
    if (totalImageCount && offset + limit < totalImageCount) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set("offset", (offset + limit).toString());
        next.set("limit", limit.toString());
        return next;
      });
      setSelectedImageIds([]);
    }
  };

  const handlePreviousPage = () => {
    const newOffset = Math.max(0, offset - limit);
    setSearchParams((prev) => {
      const prevParams = new URLSearchParams(prev);
      prevParams.set("offset", newOffset.toString());
      prevParams.set("limit", limit.toString());
      return prevParams;
    });
    setSelectedImageIds([]);
  };

  const handleAddToAlbum = async (albumId: number, imageIds: number[]) => {
    addToAlbumMutation.mutate({ albumId, imageIds });
  };

  if (isLoadingPet) {
    return (
      <Container className="mt-4 text-center">
        <Spinner animation="border" />
        <p>Loading pet details...</p>
      </Container>
    );
  }

  if (isErrorPet || !pet) {
    return (
      <Container className="mt-4">
        <Alert variant="danger">{(errorPet as Error)?.message || "Pet not found"}</Alert>
        <Button onClick={() => navigate("/pets")}>Back to Pets</Button>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <title>Memoria - {pet.name}</title>
      <h2>{pet.name}</h2>

      <p>{pet.description || <span className="text-muted">No description</span>}</p>
      <p>
        <strong>Type:</strong>{" "}
        {pet.pet_type ? pet.pet_type.charAt(0).toUpperCase() + pet.pet_type.slice(1) : "Unknown"}
      </p>
      <p>
        <strong>Created:</strong> {formatDate(profile, pet.created_at)}
      </p>
      <p>
        <strong>Updated:</strong> {formatDate(profile, pet.updated_at)}
      </p>

      <Button className="mb-3" onClick={() => setShowEditModal(true)}>
        Edit
      </Button>

      <EditPetModal
        show={showEditModal}
        handleClose={() => setShowEditModal(false)}
        pet={pet}
        onSaveSuccess={(updated) => {
          queryClient.setQueryData(["pet", pet.id], updated);
          setShowEditModal(false);
        }}
      />

      <hr className="my-4" />
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h3>Images ({totalImageCount})</h3>
        {selectedImageIds.length > 0 && (
          <Button variant="primary" onClick={() => setShowAlbumModal(true)}>
            Add {selectedImageIds.length} selected to album
          </Button>
        )}
      </div>

      {isLoadingImageIds || isLoadingImages ? (
        <div className="text-center my-4">
          <Spinner animation="border" />
          <p>Loading images...</p>
        </div>
      ) : isErrorImageIds || isErrorImages ? (
        <Alert variant="danger">
          Failed to load images: {(errorImageIds || errorImages)?.message}
        </Alert>
      ) : images && images.length > 0 ? (
        <>
          <SelectableImageWall
            images={images}
            onImageClick={(imgId) => navigate(`/images/${imgId}`)}
            columns={getGridColumns(limit as ImagesPerPageChoices)}
            onSelectionChange={setSelectedImageIds}
          />
          {totalImageCount > limit && (
            <Row className="mt-4 mb-4 justify-content-center">
              <Col xs="auto">
                <Button onClick={handlePreviousPage} disabled={offset === 0}>
                  Previous
                </Button>
              </Col>
              <Col xs="auto" className="d-flex align-items-center">
                Page {currentPage} of {totalPages}
              </Col>
              <Col xs="auto">
                <Button onClick={handleNextPage} disabled={offset + limit >= totalImageCount}>
                  Next
                </Button>
              </Col>
            </Row>
          )}
        </>
      ) : (
        <Alert variant="info">No images found for this pet.</Alert>
      )}

      <AddToAlbumModal
        show={showAlbumModal}
        onHide={() => setShowAlbumModal(false)}
        selectedImageIds={selectedImageIds}
        onAddToAlbum={handleAddToAlbum}
        isLoading={addToAlbumMutation.isPending}
        isError={addToAlbumMutation.isError}
        error={addToAlbumMutation.error}
      />
    </Container>
  );
};

export default PetDetailsPage;
