import { keepPreviousData, useQuery } from "@tanstack/react-query"; // Import keepPreviousData
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
  Pagination,
  Spinner,
  Table,
  Tooltip,
} from "react-bootstrap";
import { useNavigate, useSearchParams } from "react-router-dom";

import type {
  AlbumBasicReadOutSchema,
  AlbumCreateInSchema,
  GroupOutSchema,
  PagedAlbumBasicReadOutSchema,
} from "../api"; // Note the correction to PagedAlbumBasicReadOutSchema

import { createAlbum, getAllAlbums, listGroups } from "../api";
import { useAuth } from "../hooks/useAuth";

const AlbumsPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { profile } = useAuth();

  const [groups, setGroups] = useState<GroupOutSchema[]>([]);
  const [loadingGroups, setLoadingGroups] = useState<boolean>(true);
  const [errorGroups, setErrorGroups] = useState<string | null>(null);

  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [newAlbumData, setNewAlbumData] = useState<AlbumCreateInSchema>({
    name: "",
    description: "",
    view_group_ids: [],
    edit_group_ids: [],
  });
  const [creatingAlbum, setCreatingAlbum] = useState<boolean>(false);
  const [createAlbumError, setCreateAlbumError] = useState<string | null>(null);

  // State for search term
  const [searchTerm, setSearchTerm] = useState(searchParams.get("album_name") || "");
  // Ref for the search input to manage debounce
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Get pagination parameters from URL or defaults
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = profile?.items_per_page || 10; // Default to 10 if not in profile

  // Calculate offset based on current page and page size
  const offset = (currentPage - 1) * pageSize;

  // Fetch albums using useQuery
  const {
    data: albumsData,
    isLoading: isLoadingAlbums,
    isError: isErrorAlbums,
    error: albumsError,
    refetch: refetchAlbums,
  } = useQuery<PagedAlbumBasicReadOutSchema, Error>({
    // Corrected type for useQuery
    queryKey: ["albums", currentPage, pageSize, searchTerm],
    queryFn: async ({ signal }) => {
      const response = await getAllAlbums({
        query: {
          limit: pageSize,
          offset: offset,
          album_name: searchTerm || undefined, // Pass search term to backend
        },
        signal, // Pass the AbortController signal to the fetch request
      });
      return response.data as PagedAlbumBasicReadOutSchema;
    },
    placeholderData: keepPreviousData, // Corrected usage for placeholderData
    staleTime: 5 * 60 * 1000, // Data considered fresh for 5 minutes
  });

  // Fetch groups on component mount (no change here, still using useEffect for this static data)
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoadingGroups(true);
        const data = await listGroups();
        setGroups(data.data || []);
        setErrorGroups(null);
      } catch (error) {
        console.error("Failed to fetch groups:", error);
        setErrorGroups("Failed to load groups.");
      } finally {
        setLoadingGroups(false);
      }
    };

    fetchGroups();
  }, []);

  // Debounce effect for search term
  useEffect(() => {
    const handler = setTimeout(() => {
      const newParams = new URLSearchParams(searchParams);
      if (searchTerm) {
        newParams.set("album_name", searchTerm);
      } else {
        newParams.delete("album_name");
      }
      // Reset to first page when search term changes
      newParams.set("page", "1");
      setSearchParams(newParams);
    }, 500); // 500ms debounce

    return () => {
      clearTimeout(handler);
    };
  }, [searchTerm, searchParams, setSearchParams]);

  const handleShowModal = () => {
    setShowCreateModal(true);
    // Reset form data and errors when showing modal
    setNewAlbumData({
      name: "",
      description: "",
      view_group_ids: [],
      edit_group_ids: [],
    });
    setCreateAlbumError(null);
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
        // Convert string value from select option to number
        selectedValues.push(Number(options[i].value));
      }
    }
    setNewAlbumData((prevData) => ({
      ...prevData,
      [field]: selectedValues,
    }));
  };

  const handleCreateAlbum = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent default form submission

    if (!newAlbumData.name) {
      setCreateAlbumError("Album name is required.");
      return;
    }

    try {
      setCreatingAlbum(true);
      setCreateAlbumError(null);
      await createAlbum({ body: newAlbumData });
      refetchAlbums(); // Re-fetch albums to show the new one
      handleCloseModal(); // Close modal on success
    } catch (error) {
      console.error("Failed to create album:", error);
      setCreateAlbumError("Failed to create album. Please check the details and try again.");
    } finally {
      setCreatingAlbum(false);
    }
  };

  // Handler for navigating to the album details page
  const handleViewAlbum = (albumId: number) => {
    navigate(`/albums/${albumId}`); // Navigate to the details route
  };

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    setSearchParams(newParams);
    window.scrollTo(0, 0);
  };

  // Calculate total pages
  const totalPages = albumsData ? Math.ceil(albumsData.count / pageSize) : 0;

  const renderPaginationItems = () => {
    const items = [];
    if (totalPages === 0) return null;

    items.push(
      <Pagination.Prev
        key="prev"
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
      />,
    );

    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);

    if (startPage > 1) {
      items.push(
        <Pagination.Item key={1} active={currentPage === 1} onClick={() => handlePageChange(1)}>
          1
        </Pagination.Item>,
      );
      if (startPage > 2) {
        items.push(<Pagination.Ellipsis key="ellipsis-start" />);
      }
    }

    for (let page = startPage; page <= endPage; page++) {
      items.push(
        <Pagination.Item
          key={page}
          active={page === currentPage}
          onClick={() => handlePageChange(page)}
        >
          {page}
        </Pagination.Item>,
      );
    }

    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        items.push(<Pagination.Ellipsis key="ellipsis-end" />);
      }
      items.push(
        <Pagination.Item
          key={totalPages}
          active={currentPage === totalPages}
          onClick={() => handlePageChange(totalPages)}
        >
          {totalPages}
        </Pagination.Item>,
      );
    }

    items.push(
      <Pagination.Next
        key="next"
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      />,
    );
    return <Pagination>{items}</Pagination>;
  };

  // Function to truncate description
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

      {/* Defensive check for albumsData and albumsData.items */}
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

          {totalPages > 1 && (
            <div className="d-flex justify-content-center mt-4">{renderPaginationItems()}</div>
          )}

          <div className="mt-3 text-muted">
            Showing {offset + 1}-{/* Also ensure albumsData is checked before accessing count */}
            {Math.min(offset + pageSize, albumsData.count)} of {albumsData.count} albums
          </div>
        </>
      )}

      {/* Create Album Modal */}
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
              <Form.Label>Viewable by Groups (Optional)</Form.Label>
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
              <Form.Label>Editable by Groups (Optional)</Form.Label>
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
