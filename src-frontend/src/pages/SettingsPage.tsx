// src/pages/SettingsPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Form, Row, Spinner, Table } from "react-bootstrap";
import { useForm } from "react-hook-form";
import { Navigate } from "react-router-dom";

import type {
  GroupOutSchema,
  ImageScaledSideMaxEnum,
  SiteSettingsUpdateSchemaIn,
  ThumbnailSizeEnum,
  UserOutSchema,
} from "../api";

import {
  getSystemSettingsOptions,
  listGroupsOptions,
  updateSystemSettingsMutation,
  usersGroupsListOptions,
  usersListOptions,
} from "../api/@tanstack/react-query.gen";
import CreateGroupModal from "../components/group-management/CreateGroupModal";
import DeleteGroupModal from "../components/group-management/DeleteGroupModal";
import EditGroupModal from "../components/group-management/EditGroupModal";
import CreateUserModal from "../components/user-management/CreateUserModal";
import EditUserModal from "../components/user-management/EditUserModal";
import ManageGroupsModal from "../components/user-management/ManageGroupsModal";
import { useAuth } from "../hooks/useAuth";
import { formatDate } from "../utils/formatDate";

type SystemSettingsFormData = {
  large_image_max_size: ImageScaledSideMaxEnum;
  large_image_quality: number;
  thumbnail_max_size: ThumbnailSizeEnum;
};

const SettingsPage: React.FC = () => {
  const { user: currentUser, profile } = useAuth();
  const queryClient = useQueryClient();

  // React Hook Form setup for system settings
  const {
    register,
    handleSubmit,
    reset,
    formState: { isDirty, dirtyFields },
  } = useForm<SystemSettingsFormData>();

  // --- User Management State (just visibility and selection) ---
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showManageUserGroupsModal, setShowManageUserGroupsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserOutSchema | null>(null);

  // --- Group Management State (just visibility and selection) ---
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [showEditGroupModal, setShowEditGroupModal] = useState(false);
  const [showDeleteGroupModal, setShowDeleteGroupModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<GroupOutSchema | null>(null);

  // --- System Settings State (kept here since form is on this page) ---
  const [systemSettingsError, setSystemSettingsError] = useState<string | null>(null);
  const [systemSettingsSuccess, setSystemSettingsSuccess] = useState<string | null>(null);

  // --- Queries using generated options ---
  const {
    data: systemSettings,
    isLoading: systemSettingsLoading,
    error: systemSettingsQueryError,
  } = useQuery(getSystemSettingsOptions());

  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersQueryError,
  } = useQuery(usersListOptions());

  const {
    data: groups = [],
    isLoading: groupsLoading,
    error: groupsQueryError,
  } = useQuery(listGroupsOptions());

  const { data: userGroups = [], isLoading: userGroupsLoading } = useQuery({
    ...usersGroupsListOptions({
      path: { user_id: selectedUser?.id ?? 0 },
    }),
    enabled: !!selectedUser && showManageUserGroupsModal,
  });

  const userGroupIds = userGroups.map((group) => group.id);

  // Reset form when systemSettings data is loaded
  useEffect(() => {
    if (systemSettings) {
      reset({
        large_image_max_size: systemSettings.large_image_max_size,
        large_image_quality: systemSettings.large_image_quality,
        thumbnail_max_size: systemSettings.thumbnail_max_size,
      });
    }
  }, [systemSettings, reset]);

  // --- System Settings Mutation (kept here since form is on this page) ---
  const systemSettingsMutation = useMutation({
    ...updateSystemSettingsMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["getSystemSettings"] });
      setSystemSettingsError(null);
      setSystemSettingsSuccess("System settings updated successfully!");
      setTimeout(() => setSystemSettingsSuccess(null), 3000);
    },
    onError: (err) => {
      setSystemSettingsError(err.message || "Failed to update system settings.");
      setSystemSettingsSuccess(null);
    },
  });

  // --- System Settings Handler ---
  const onSubmitSystemSettings = (data: SystemSettingsFormData) => {
    const changedFields: Partial<SiteSettingsUpdateSchemaIn> = {};

    if (dirtyFields.large_image_max_size) {
      changedFields.large_image_max_size = data.large_image_max_size;
    }
    if (dirtyFields.large_image_quality) {
      changedFields.large_image_quality = data.large_image_quality;
    }
    if (dirtyFields.thumbnail_max_size) {
      changedFields.thumbnail_max_size = data.thumbnail_max_size;
    }

    if (Object.keys(changedFields).length > 0) {
      setSystemSettingsError(null);
      setSystemSettingsSuccess(null);
      systemSettingsMutation.mutate({ body: changedFields as SiteSettingsUpdateSchemaIn });
    }
  };

  // --- User Management Modal Handlers (simplified - no error/loading management) ---
  const handleShowCreateUserModal = () => setShowCreateUserModal(true);
  const handleCloseCreateUserModal = () => setShowCreateUserModal(false);

  const handleShowEditUserModal = (user: UserOutSchema) => {
    setSelectedUser(user);
    setShowEditUserModal(true);
  };

  const handleCloseEditUserModal = () => {
    setShowEditUserModal(false);
    setSelectedUser(null);
  };

  const handleShowManageUserGroupsModal = (user: UserOutSchema) => {
    setSelectedUser(user);
    setShowManageUserGroupsModal(true);
  };

  const handleCloseManageUserGroupsModal = () => {
    setShowManageUserGroupsModal(false);
    setSelectedUser(null);
  };

  // --- Group Management Modal Handlers (simplified) ---
  const handleShowCreateGroupModal = () => setShowCreateGroupModal(true);
  const handleCloseCreateGroupModal = () => setShowCreateGroupModal(false);

  const handleShowEditGroupModal = (group: GroupOutSchema) => {
    setSelectedGroup(group);
    setShowEditGroupModal(true);
  };

  const handleCloseEditGroupModal = () => {
    setShowEditGroupModal(false);
    setSelectedGroup(null);
  };

  const handleShowDeleteGroupModal = (group: GroupOutSchema) => {
    setSelectedGroup(group);
    setShowDeleteGroupModal(true);
  };

  const handleCloseDeleteGroupModal = () => {
    setShowDeleteGroupModal(false);
    setSelectedGroup(null);
  };

  // Define the actual enum values for iteration
  const imageSizeOptions = [
    { value: 768, label: "768px (Tablet/Small Screen)" },
    { value: 1024, label: "1024px (Tablet Landscape/Laptop)" },
    { value: 1920, label: "1920px (HD/Desktop)" },
    { value: 2560, label: "2560px (QHD/Large Desktop)" },
    { value: 3840, label: "3840px (4K/HiDPI Desktop)" },
  ];

  const thumbnailSizeOptions = [
    { value: 128, label: "128px (Tiny)" },
    { value: 256, label: "256px (Small)" },
    { value: 512, label: "512px (Medium)" },
    { value: 640, label: "640px (Large)" },
    { value: 800, label: "800px (X-Large)" },
  ];

  // --- Auth Check ---
  if (currentUser === undefined) {
    return (
      <div className="d-flex justify-content-center mt-5">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading User...</span>
        </Spinner>
      </div>
    );
  }

  if (currentUser === null || (!currentUser.is_staff && !currentUser.is_superuser)) {
    return <Navigate to="/" replace />;
  }

  // --- Render ---
  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">Application Settings</Card.Header>
        <Card.Body>
          <Alert variant="info">This page is available to staff and superusers only.</Alert>

          {/* System Settings Section */}
          <h3 className="mt-4">System Settings</h3>
          {systemSettingsError && <Alert variant="danger">{systemSettingsError}</Alert>}
          {systemSettingsSuccess && <Alert variant="success">{systemSettingsSuccess}</Alert>}

          {systemSettingsLoading ? (
            <div className="d-flex justify-content-center">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading System Settings...</span>
              </Spinner>
            </div>
          ) : systemSettingsQueryError ? (
            <Alert variant="danger">
              {systemSettingsQueryError instanceof Error
                ? systemSettingsQueryError.message
                : "Failed to load system settings."}
            </Alert>
          ) : systemSettings ? (
            <Card className="mb-4">
              <Card.Header>
                <h5 className="mb-0">Image Processing Settings</h5>
              </Card.Header>
              <Card.Body>
                <Form onSubmit={handleSubmit(onSubmitSystemSettings)}>
                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Large Image Maximum Size</Form.Label>
                        <Form.Select
                          {...register("large_image_max_size", {
                            valueAsNumber: true,
                          })}
                        >
                          {imageSizeOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Form.Select>
                        <Form.Text className="text-muted">
                          The largest side dimension of generated large images
                        </Form.Text>
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Large Image Quality</Form.Label>
                        <Form.Control
                          type="number"
                          min="1"
                          max="100"
                          {...register("large_image_quality", {
                            valueAsNumber: true,
                            min: 1,
                            max: 100,
                          })}
                        />
                        <Form.Text className="text-muted">
                          The WebP quality setting for generated large images (1-100)
                        </Form.Text>
                      </Form.Group>
                    </Col>
                  </Row>
                  <Row>
                    <Col md={6}>
                      <Form.Group className="mb-3">
                        <Form.Label>Thumbnail Maximum Size</Form.Label>
                        <Form.Select
                          {...register("thumbnail_max_size", {
                            valueAsNumber: true,
                          })}
                        >
                          {thumbnailSizeOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Form.Select>
                        <Form.Text className="text-muted">
                          The largest side dimension of generated image thumbnails
                        </Form.Text>
                      </Form.Group>
                    </Col>
                  </Row>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={systemSettingsMutation.isPending || !isDirty}
                  >
                    {systemSettingsMutation.isPending ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-2" />
                        Updating...
                      </>
                    ) : (
                      "Update System Settings"
                    )}
                  </Button>
                </Form>
              </Card.Body>
            </Card>
          ) : null}

          {/* User Management Section */}
          <h3 className="mt-4">User Management</h3>
          <Button variant="primary" onClick={handleShowCreateUserModal} className="mb-3">
            Create New User
          </Button>

          {usersLoading && !users.length ? (
            <div className="d-flex justify-content-center">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading Users...</span>
              </Spinner>
            </div>
          ) : usersQueryError ? (
            <Alert variant="danger">
              {usersQueryError instanceof Error
                ? usersQueryError.message
                : "Failed to load users."}
            </Alert>
          ) : (
            <Table striped bordered hover responsive className="mt-3">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Email</th>
                  <th>Active</th>
                  <th>Staff</th>
                  <th>Superuser</th>
                  <th>Last Login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.username}</td>
                    <td>{user.first_name}</td>
                    <td>{user.last_name}</td>
                    <td>{user.email}</td>
                    <td>{(user.is_active ?? true) ? "Yes" : "No"}</td>
                    <td>{(user.is_staff ?? false) ? "Yes" : "No"}</td>
                    <td>{(user.is_superuser ?? false) ? "Yes" : "No"}</td>
                    <td>{user.last_login ? formatDate(profile, user.last_login) : "Never"}</td>
                    <td>
                      {(currentUser.is_staff || currentUser.is_superuser) && (
                        <>
                          <Button
                            variant="secondary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleShowEditUserModal(user)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="info"
                            size="sm"
                            onClick={() => handleShowManageUserGroupsModal(user)}
                          >
                            Groups
                          </Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {users.length === 0 && !usersLoading && !usersQueryError && (
                  <tr>
                    <td colSpan={10} className="text-center">
                      No users found.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}

          {/* Group Management Section */}
          <h3 className="mt-4">Group Management</h3>
          <Button variant="primary" onClick={handleShowCreateGroupModal} className="mb-3">
            Create New Group
          </Button>

          {groupsLoading && !groups.length ? (
            <div className="d-flex justify-content-center">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading Groups...</span>
              </Spinner>
            </div>
          ) : groupsQueryError ? (
            <Alert variant="danger">
              {groupsQueryError instanceof Error
                ? groupsQueryError.message
                : "Failed to load groups."}
            </Alert>
          ) : (
            <Table striped bordered hover responsive className="mt-3">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <tr key={group.id}>
                    <td>{group.id}</td>
                    <td>{group.name}</td>
                    <td>
                      {(currentUser.is_staff || currentUser.is_superuser) && (
                        <>
                          <Button
                            variant="secondary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleShowEditGroupModal(group)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleShowDeleteGroupModal(group)}
                          >
                            Delete
                          </Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {groups.length === 0 && !groupsLoading && !groupsQueryError && (
                  <tr>
                    <td colSpan={3} className="text-center">
                      No groups found.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* --- User Management Modals (simplified props) --- */}
      <CreateUserModal show={showCreateUserModal} handleClose={handleCloseCreateUserModal} />

      {selectedUser && (
        <EditUserModal
          show={showEditUserModal}
          handleClose={handleCloseEditUserModal}
          user={selectedUser}
        />
      )}

      {selectedUser && (
        <ManageGroupsModal
          show={showManageUserGroupsModal}
          handleClose={handleCloseManageUserGroupsModal}
          user={selectedUser}
          allGroups={groups}
          userGroupIds={userGroupIds}
          userGroupsLoading={userGroupsLoading}
        />
      )}

      {/* --- Group Management Modals (simplified props) --- */}
      <CreateGroupModal show={showCreateGroupModal} handleClose={handleCloseCreateGroupModal} />

      {selectedGroup && (
        <EditGroupModal
          show={showEditGroupModal}
          handleClose={handleCloseEditGroupModal}
          group={selectedGroup}
        />
      )}

      {selectedGroup && (
        <DeleteGroupModal
          show={showDeleteGroupModal}
          handleClose={handleCloseDeleteGroupModal}
          group={selectedGroup}
        />
      )}
    </Container>
  );
};

export default SettingsPage;
