import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Button,
  Container,
  Form,
  FormControl,
  InputGroup,
  Modal,
  OverlayTrigger,
  Spinner,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type { AlbumBasicReadOutSchema, AlbumCreateInSchema } from "../api";

import {
  createAlbumMutation,
  getAllAlbumsOptions,
  listGroupsOptions,
} from "../api/@tanstack/react-query.gen";
import PaginationComponent from "../components/common/PaginationComponent";
import { useAuth } from "../hooks/useAuth";

const AlbumsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();
  const queryClient = useQueryClient();

  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newAlbumData, setNewAlbumData] = useState<AlbumCreateInSchema>({
    name: "",
    description: "",
    view_group_ids: [],
    edit_group_ids: [],
  });
  const [clientCreateAlbumError, setClientCreateAlbumError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState(searchParams.get("album_name") || "");
  const searchInputRef = useRef<HTMLInputElement>(null);

  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10;

  const offset = (currentPage - 1) * pageSize;

  const {
    data: albumsData,
    isLoading: isLoadingAlbums,
    isError: isErrorAlbums,
    error: albumsError,
  } = useQuery({
    ...getAllAlbumsOptions({
      query: {
        limit: pageSize,
        offset: offset,
        album_name: searchTerm || undefined,
      },
    }),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });

  const {
    data: groups = [],
    isLoading: loadingGroups,
    isError: isErrorGroups,
  } = useQuery(listGroupsOptions());
  const errorGroups = isErrorGroups ? "Failed to load groups." : null;

  useEffect(() => {
    const handler = setTimeout(() => {
      const newParams = new URLSearchParams(searchParams);
      if (searchTerm) {
        newParams.set("album_name", searchTerm);
      } else {
        newParams.delete("album_name");
      }
      newParams.set("page", "1");
      setSearchParams(newParams);
    }, 500);

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, searchParams, setSearchParams]);

  const handleShowModal = () => {
    setShowCreateModal(true);
    setNewAlbumData({
      name: "",
      description: "",
      view_group_ids: [],
      edit_group_ids: [],
    });
    setClientCreateAlbumError(null);
  };

  const handleCloseModal = () => setShowCreateModal(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewAlbumData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleGroupSelectChange = (
    e: React.ChangeEvent<HTMLSelectElement>,
    field: "view_group_ids" | "edit_group_ids",
  ) => {
    const options = e.target.options;
    const selectedValues: number[] = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selectedValues.push(Number(options[i].value));
      }
    }
    setNewAlbumData((prevData) => ({
      ...prevData,
      [field]: selectedValues,
    }));
  };

  const {
    mutateAsync: createAlbumAsync,
    isPending: creatingAlbum,
    error: createMutationError,
  } = useMutation({
    ...createAlbumMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
      handleCloseModal();
    },
  });

  const createAlbumError =
    clientCreateAlbumError ||
    (createMutationError
      ? "Failed to create album. Please check the details and try again."
      : null);

  const handleCreateAlbum = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newAlbumData.name) {
      setClientCreateAlbumError("Album name is required.");
      return;
    }

    try {
      setClientCreateAlbumError(null);
      await createAlbumAsync({ body: newAlbumData });
    } catch (error) {
      console.error("Failed to create album:", error);
    }
  };

  const handleViewAlbum = (albumId: number) => {
    navigate(`/albums/${albumId}`);
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    window.scrollTo(0, 0);
  };

  const totalPages = albumsData ? Math.ceil(albumsData.count / pageSize) : 0;

  const truncateDescription = (text: string | undefined, maxLength: number) => {
    if (!text) return "N/A";
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  };

  return (
    <Container className="mt-4">
      <title>Memoria - All Albums</title>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Albums</h2>
        <Button variant="primary" onClick={handleShowModal}>
          Create New Album
        </Button>
      </div>

      <InputGroup className="mb-3">
        <FormControl
          placeholder="Search by album name..."
          aria-label="Search by album name"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          ref={searchInputRef}
        />
        <Button variant="outline-secondary" disabled>
          <i className="bi bi-search"></i>
        </Button>
      </InputGroup>

      {isLoadingAlbums && (
        <div className="text-center">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading Albums...</span>
          </Spinner>
          <p>Loading albums...</p>
        </div>
      )}

      {isErrorAlbums && <Alert variant="danger">Error: {(albumsError as Error).message}</Alert>}

      {!isLoadingAlbums && !isErrorAlbums && (!albumsData || albumsData.items.length === 0) && (
        <Alert variant="info">
          No albums found matching your criteria. Click "Create New Album" to add one.
        </Alert>
      )}

      {albumsData && albumsData.items && albumsData.items.length > 0 && (
        <>
          <Table striped bordered hover responsive className="mt-3">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Image Count</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {albumsData.items.map((album: AlbumBasicReadOutSchema) => (
                <tr key={album.id}>
                  <td>{album.name}</td>
                  <td>
                    {album.description && album.description.length > 50 ? (
                      <OverlayTrigger
                        placement="top"
                        delay={{ show: 250, hide: 400 }}
                        overlay={
                          <Tooltip id={`tooltip-album-${album.id}`}>{album.description}</Tooltip>
                        }
                      >
                        <span>{truncateDescription(album.description, 50)}</span>
                      </OverlayTrigger>
                    ) : (
                      album.description || "N/A"
                    )}
                  </td>
                  <td>{album.image_count}</td>
                  <td>
                    <Button variant="primary" size="sm" onClick={() => handleViewAlbum(album.id)}>
                      View Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          {/* Use the PaginationComponent here */}
          <PaginationComponent
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />

          <div className="mt-3 text-muted">
            Showing {offset + 1}-{Math.min(offset + pageSize, albumsData.count)} of{" "}
            {albumsData.count} albums
          </div>
        </>
      )}

      <Modal show={showCreateModal} onHide={handleCloseModal}>
        <Modal.Header closeButton>
          <Modal.Title>Create New Album</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleCreateAlbum}>
          <Modal.Body>
            {createAlbumError && <Alert variant="danger">{createAlbumError}</Alert>}
            <Form.Group className="mb-3" controlId="newAlbumName">
              <Form.Label>Album Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="Enter album name"
                name="name"
                value={newAlbumData.name}
                onChange={handleInputChange}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="newAlbumDescription">
              <Form.Label>Description (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Enter description"
                name="description"
                value={newAlbumData.description || ""}
                onChange={handleInputChange}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="newAlbumViewGroups">
              <Form.Label>Viewable by Groups</Form.Label>
              {loadingGroups ? (
                <p>Loading groups...</p>
              ) : errorGroups ? (
                <Alert variant="warning">{errorGroups}</Alert>
              ) : (
                <Form.Select
                  multiple
                  name="view_group_ids"
                  value={newAlbumData.view_group_ids?.map(String) || []}
                  onChange={(e) => handleGroupSelectChange(e, "view_group_ids")}
                  disabled={groups.length === 0}
                >
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </Form.Select>
              )}
              <Form.Text className="text-muted">
                Hold Ctrl (or Cmd) to select multiple groups.
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-3" controlId="newAlbumEditGroups">
              <Form.Label>Editable by Groups</Form.Label>
              {loadingGroups ? (
                <p>Loading groups...</p>
              ) : errorGroups ? (
                <Alert variant="warning">{errorGroups}</Alert>
              ) : (
                <Form.Select
                  multiple
                  name="edit_group_ids"
                  value={newAlbumData.edit_group_ids?.map(String) || []}
                  onChange={(e) => handleGroupSelectChange(e, "edit_group_ids")}
                  disabled={groups.length === 0}
                >
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </Form.Select>
              )}
              <Form.Text className="text-muted">
                Hold Ctrl (or Cmd) to select multiple groups.
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal} disabled={creatingAlbum}>
              Close
            </Button>
            <Button variant="primary" type="submit" disabled={creatingAlbum || !newAlbumData.name}>
              {creatingAlbum ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                    className="me-1"
                  />
                  Creating...
                </>
              ) : (
                "Create Album"
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default AlbumsPage;
