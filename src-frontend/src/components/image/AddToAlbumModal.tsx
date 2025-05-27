import { useQuery } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Button, Form, ListGroup, Modal, Spinner } from "react-bootstrap";

import type { AlbumBasicReadOutSchema } from "../../api";

import { getAllAlbums } from "../../api";

interface AddToAlbumModalProps {
  show: boolean;
  onHide: () => void;
  selectedImageIds: number[];
  onAddToAlbum: (albumId: number, imageIds: number[]) => Promise<void>;
  isLoading?: boolean;
  isError?: boolean;
  error?: unknown;
}

const AddToAlbumModal: React.FC<AddToAlbumModalProps> = ({
  show,
  onHide,
  selectedImageIds,
  onAddToAlbum,
  isLoading = false,
  isError = false,
  error,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAlbum, setSelectedAlbum] = useState<AlbumBasicReadOutSchema | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Reset state when modal is opened/closed
  useEffect(() => {
    if (!show) {
      setSearchQuery("");
      setSelectedAlbum(null);
      setErrorMessage(null);
    }
  }, [show]);

  // Use react-query for album search
  const {
    data: searchResults = [],
    isLoading: isSearching,
    error: searchError,
  } = useQuery({
    queryKey: ["albums", "search", searchQuery],
    queryFn: async (): Promise<AlbumBasicReadOutSchema[]> => {
      if (searchQuery.trim().length < 2) {
        return [];
      }
      const results = await getAllAlbums({ query: { album_name: searchQuery } });
      return results.data || [];
    },
    enabled: searchQuery.trim().length >= 2 && show,
    staleTime: 30000, // Cache results for 30 seconds
  });

  // Effect to set error message if search fails
  useEffect(() => {
    if (searchError) {
      console.error("Error searching albums:", searchError);
      setErrorMessage("Failed to search albums. Please try again.");
    } else if (isError && error) {
      console.error("Error adding images to album:", error);
      setErrorMessage("Failed to add images to album. Please try again.");
    } else {
      setErrorMessage(null);
    }
  }, [searchError, isError, error]);

  const handleSelectAlbum = (album: AlbumBasicReadOutSchema) => {
    setSelectedAlbum(album);
  };

  const handleAddToAlbum = async () => {
    if (!selectedAlbum || selectedImageIds.length === 0) return;

    try {
      await onAddToAlbum(selectedAlbum.id, selectedImageIds);
    } catch (error) {
      console.error("Error adding images to album:", error);
      setErrorMessage("Failed to add images to album. Please try again.");
    }
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Add to Album</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p>
          Selected {selectedImageIds.length} image{selectedImageIds.length !== 1 ? "s" : ""} to add
          to album
        </p>

        <Form>
          <Form.Group className="mb-3">
            <Form.Label>Search Albums</Form.Label>
            <Form.Control
              type="text"
              placeholder="Type to search for albums..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            <Form.Text className="text-muted">Type at least 2 characters to search</Form.Text>
          </Form.Group>
        </Form>

        {isSearching && (
          <div className="text-center py-3">
            <Spinner animation="border" size="sm" role="status">
              <span className="visually-hidden">Searching...</span>
            </Spinner>
            <span className="ms-2">Searching...</span>
          </div>
        )}

        {!isSearching && searchResults.length > 0 && (
          <ListGroup className="mt-3">
            {searchResults.map((album) => (
              <ListGroup.Item
                key={album.id}
                action
                active={selectedAlbum?.id === album.id}
                onClick={() => handleSelectAlbum(album)}
              >
                {album.name}
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}

        {!isSearching && searchQuery.trim().length >= 2 && searchResults.length === 0 && (
          <p className="text-muted">No albums found. Try a different search term.</p>
        )}

        {errorMessage && <div className="text-danger mt-3">{errorMessage}</div>}
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleAddToAlbum}
          disabled={!selectedAlbum || selectedImageIds.length === 0 || isLoading}
        >
          {isLoading ? (
            <>
              <Spinner animation="border" size="sm" role="status">
                <span className="visually-hidden">Adding...</span>
              </Spinner>
              <span className="ms-2">Adding...</span>
            </>
          ) : selectedAlbum ? (
            `Add to "${selectedAlbum.name}"`
          ) : (
            "Add to Album"
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default AddToAlbumModal;
