import React, { useEffect, useState } from 'react';
import {
    Container,
    Row,
    Col,
    Card,
    Button,
    Modal,
    Form,
    Spinner,
    Alert,
} from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { groupGetAll, getAlbums, createAlbum } from '../api';
import type { AlbumBasicReadOutSchema, GroupOutSchema, AlbumCreateInSchema } from '../api';

const AlbumsPage: React.FC = () => {
    const navigate = useNavigate();
    const [albums, setAlbums] = useState<AlbumBasicReadOutSchema[]>([]);
    const [loadingAlbums, setLoadingAlbums] = useState<boolean>(true);
    const [errorAlbums, setErrorAlbums] = useState<string | null>(null);

    const [groups, setGroups] = useState<GroupOutSchema[]>([]);
    const [loadingGroups, setLoadingGroups] = useState<boolean>(true);
    const [errorGroups, setErrorGroups] = useState<string | null>(null);

    const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
    const [newAlbumData, setNewAlbumData] = useState<AlbumCreateInSchema>({
        name: '',
        description: '',
        view_group_ids: [],
        edit_group_ids: [],
    });
    const [creatingAlbum, setCreatingAlbum] = useState<boolean>(false);
    const [createAlbumError, setCreateAlbumError] = useState<string | null>(null);

    // Fetch albums on component mount
    useEffect(() => {
        const fetchAlbums = async () => {
            try {
                setLoadingAlbums(true);
                const data = await getAlbums();
                setAlbums(data.data || []);
                setErrorAlbums(null);
            } catch (error) {
                console.error('Failed to fetch albums:', error);
                setErrorAlbums('Failed to load albums. Please try again.');
            } finally {
                setLoadingAlbums(false);
            }
        };

        fetchAlbums();
    }, []); // Empty dependency array means this runs once on mount

    // Fetch groups on component mount
    useEffect(() => {
        const fetchGroups = async () => {
            try {
                setLoadingGroups(true);
                const data = await groupGetAll();
                setGroups(data.data || []);
                setErrorGroups(null);
            } catch (error) {
                console.error('Failed to fetch groups:', error);
                setErrorGroups('Failed to load groups.');
            } finally {
                setLoadingGroups(false);
            }
        };

        fetchGroups();
    }, []); // Empty dependency array means this runs once on mount


    const handleShowModal = () => {
        setShowCreateModal(true);
        // Reset form data and errors when showing modal
        setNewAlbumData({
            name: '',
            description: '',
            view_group_ids: [],
            edit_group_ids: [],
        });
        setCreateAlbumError(null);
    };

    const handleCloseModal = () => setShowCreateModal(false);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setNewAlbumData(prevData => ({
            ...prevData,
            [name]: value,
        }));
    };

    const handleGroupSelectChange = (e: React.ChangeEvent<HTMLSelectElement>, field: 'view_group_ids' | 'edit_group_ids') => {
        const options = e.target.options;
        const selectedValues: number[] = [];
        for (let i = 0; i < options.length; i++) {
            if (options[i].selected) {
                // Convert string value from select option to number
                selectedValues.push(Number(options[i].value));
            }
        }
        setNewAlbumData(prevData => ({
            ...prevData,
            [field]: selectedValues,
        }));
    };

    const handleCreateAlbum = async (e: React.FormEvent) => {
        e.preventDefault(); // Prevent default form submission

        if (!newAlbumData.name) {
            setCreateAlbumError('Album name is required.');
            return;
        }

        try {
            setCreatingAlbum(true);
            setCreateAlbumError(null);
            // Pass the new album data to the API function
            const createdAlbum = await createAlbum({body: newAlbumData});
            console.log('Album created successfully:', createdAlbum);

            // Option 1: Add the new album to the existing list (if API returns the full object)
            // setAlbums(prevAlbums => [...prevAlbums, createdAlbum]);

            // Option 2: Re-fetch the entire list of albums to ensure data is fresh
             const updatedAlbums = await getAlbums();
             setAlbums(updatedAlbums.data || []);

            handleCloseModal(); // Close modal on success
        } catch (error) {
            console.error('Failed to create album:', error);
            setCreateAlbumError('Failed to create album. Please check the details and try again.');
        } finally {
            setCreatingAlbum(false);
        }
    };

        // Handler for navigating to the album details page
    const handleViewAlbum = (albumId: number) => {
        navigate(`/albums/${albumId}`); // Navigate to the details route
    };

    return (
        <Container className="mt-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Albums</h2>
                <Button variant="primary" onClick={handleShowModal}>
                    Create New Album
                </Button>
            </div>

            {loadingAlbums && (
                <div className="text-center">
                    <Spinner animation="border" role="status">
                        <span className="visually-hidden">Loading Albums...</span>
                    </Spinner>
                    <p>Loading albums...</p>
                </div>
            )}

            {errorAlbums && <Alert variant="danger">{errorAlbums}</Alert>}

            {!loadingAlbums && !errorAlbums && albums.length === 0 && (
                 <Alert variant="info">No albums found. Click "Create New Album" to add one.</Alert>
            )}

            <Row xs={1} md={2} lg={3} className="g-4">
                {albums.map((album) => (
                    <Col key={album.id}>
                        <Card className="h-100 shadow-sm" style={{ cursor: 'pointer' }}>
                            <Card.Body onClick={() => handleViewAlbum(album.id)}>
                                <Card.Title>{album.name}</Card.Title>
                                <Card.Text>
                                    {album.description || 'No description provided.'}
                                </Card.Text>
                                <Card.Text>
                                    <strong>Images:</strong> {album.image_count}
                                </Card.Text>
                            </Card.Body>
                        </Card>
                    </Col>
                ))}
            </Row>

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
                                value={newAlbumData.description || ''}
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
                                    value={newAlbumData.view_group_ids?.map(String) || []} // Convert numbers to strings for select value
                                    onChange={(e) => handleGroupSelectChange(e, 'view_group_ids')}
                                    disabled={groups.length === 0}
                                >
                                    {groups.map(group => (
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
                                     value={newAlbumData.edit_group_ids?.map(String) || []} // Convert numbers to strings for select value
                                    onChange={(e) => handleGroupSelectChange(e, 'edit_group_ids')}
                                     disabled={groups.length === 0}
                                >
                                    {groups.map(group => (
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
                                'Create Album'
                            )}
                        </Button>
                    </Modal.Footer>
                </Form>
            </Modal>
        </Container>
    );
};

export default AlbumsPage;
