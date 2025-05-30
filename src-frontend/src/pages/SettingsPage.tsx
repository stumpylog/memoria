// src/pages/SettingsPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Form, Row, Spinner, Table } from "react-bootstrap";
import { useForm } from "react-hook-form";
import { Navigate } from "react-router-dom";

// Types
import type {
  GroupCreateInSchema,
  GroupOutSchema,
  GroupUpdateInSchema,
  ImageScaledSideMaxEnum,
  SiteSettingsUpdateSchemaIn,
  ThumbnailSizeEnum,
  UserGroupAssignInSchema,
  UserInCreateSchemaWritable,
  UserOutSchema,
  UserUpdateInSchemeWritable,
} from "../api";

// API functions
import {
  createGroups,
  deleteGroup,
  getSystemSettings,
  listGroups,
  updateGroup,
  updateSystemSettings,
  usersCreate,
  usersGroupsList,
  usersGroupsUpdate,
  usersList,
  usersUpdate,
} from "../api";
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

  // React Hook Form setup
  const {
    register,
    handleSubmit,
    reset,
    formState: { isDirty, dirtyFields },
  } = useForm<SystemSettingsFormData>();

  // --- User Management State ---
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showManageUserGroupsModal, setShowManageUserGroupsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserOutSchema | null>(null);
  const [userError, setUserError] = useState<string | null>(null);

  // --- Group Management State ---
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [showEditGroupModal, setShowEditGroupModal] = useState(false);
  const [showDeleteGroupModal, setShowDeleteGroupModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<GroupOutSchema | null>(null);
  const [groupError, setGroupError] = useState<string | null>(null);

  // --- System Settings State ---
  const [systemSettingsError, setSystemSettingsError] = useState<string | null>(null);
  const [systemSettingsSuccess, setSystemSettingsSuccess] = useState<string | null>(null);

  // --- System Settings Query ---
  const {
    data: systemSettings,
    isLoading: systemSettingsLoading,
    error: systemSettingsQueryError,
  } = useQuery({
    queryKey: ["systemSettings"],
    queryFn: async () => {
      const response = await getSystemSettings();
      return response?.data;
    },
  });

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

  // --- User Management Queries ---
  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersQueryError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const response = await usersList();
      return response?.data || [];
    },
  });

  const { data: userGroupIds = [], isLoading: userGroupsLoading } = useQuery({
    queryKey: ["userGroups", selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return [];
      const response = await usersGroupsList({ path: { user_id: selectedUser.id } });
      return response?.data?.map((group) => group.id) || [];
    },
    enabled: !!selectedUser && showManageUserGroupsModal,
  });

  const {
    data: groups = [],
    isLoading: groupsLoading,
    error: groupsQueryError,
  } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      const response = await listGroups();
      return response?.data || [];
    },
  });

  // --- System Settings Mutation ---
  const updateSystemSettingsMutation = useMutation({
    mutationFn: (settingsData: SiteSettingsUpdateSchemaIn) =>
      updateSystemSettings({ body: settingsData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["systemSettings"] });
      setSystemSettingsError(null);
      setSystemSettingsSuccess("System settings updated successfully!");
      // Clear success message after 3 seconds
      setTimeout(() => setSystemSettingsSuccess(null), 3000);
    },
    onError: (err: any) => {
      setSystemSettingsError(err.message || "Failed to update system settings.");
      setSystemSettingsSuccess(null);
    },
  });

  // --- User Management Mutations ---
  const createUserMutation = useMutation({
    mutationFn: (userData: UserInCreateSchemaWritable) => usersCreate({ body: userData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      handleCloseCreateUserModal();
    },
    onError: (err: any) => {
      setUserError(err.message || "Failed to create user.");
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, userData }: { userId: number; userData: UserUpdateInSchemeWritable }) =>
      usersUpdate({ path: { user_id: userId }, body: userData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      handleCloseEditUserModal();
    },
    onError: (err: any) => {
      setUserError(err.message || `Failed to update user.`);
    },
  });

  const updateUserGroupsMutation = useMutation({
    mutationFn: ({ userId, groupIds }: { userId: number; groupIds: UserGroupAssignInSchema[] }) =>
      usersGroupsUpdate({ path: { user_id: userId }, body: groupIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] }); // Users table might show group info
      queryClient.invalidateQueries({ queryKey: ["userGroups", selectedUser?.id] }); // Invalidate the specific user's groups
      handleCloseManageUserGroupsModal();
    },
    onError: (err: any) => {
      setUserError(err.message || `Failed to update user groups.`);
    },
  });

  // --- Group Management Mutations ---
  const createGroupMutation = useMutation({
    mutationFn: (groupData: GroupCreateInSchema) => createGroups({ body: groupData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      handleCloseCreateGroupModal();
    },
    onError: (err: any) => {
      setGroupError(err.message || "Failed to create group.");
    },
  });

  const updateGroupMutation = useMutation({
    mutationFn: ({ groupId, groupData }: { groupId: number; groupData: GroupUpdateInSchema }) =>
      updateGroup({ path: { group_id: groupId }, body: groupData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      handleCloseEditGroupModal();
    },
    onError: (err: any) => {
      setGroupError(err.message || `Failed to update group.`);
    },
  });

  const deleteGroupMutation = useMutation({
    mutationFn: (groupId: number) => deleteGroup({ path: { group_id: groupId } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      handleCloseDeleteGroupModal();
    },
    onError: (err: any) => {
      setGroupError(err.message || `Failed to delete group.`);
    },
  });

  // --- System Settings Handlers ---
  const onSubmitSystemSettings = (data: SystemSettingsFormData) => {
    // Only send fields that have been modified
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
      updateSystemSettingsMutation.mutate(changedFields as SiteSettingsUpdateSchemaIn);
    }
  };

  // --- User Management Modal Handlers ---
  const handleShowCreateUserModal = () => {
    setUserError(null);
    setShowCreateUserModal(true);
  };

  const handleCloseCreateUserModal = () => {
    setUserError(null);
    setShowCreateUserModal(false);
  };

  const handleCreateUser = async (userData: UserInCreateSchemaWritable): Promise<void> => {
    setUserError(null);
    await createUserMutation.mutateAsync(userData);
  };

  const handleShowEditUserModal = (user: UserOutSchema) => {
    setUserError(null);
    setSelectedUser(user);
    setShowEditUserModal(true);
  };

  const handleCloseEditUserModal = () => {
    setUserError(null);
    setShowEditUserModal(false);
    setSelectedUser(null);
  };

  const handleEditUser = async (
    userId: number,
    userData: UserUpdateInSchemeWritable,
  ): Promise<void> => {
    setUserError(null);
    await updateUserMutation.mutateAsync({ userId, userData });
  };

  const handleShowManageUserGroupsModal = (user: UserOutSchema) => {
    setUserError(null);
    setSelectedUser(user);
    setShowManageUserGroupsModal(true);
  };

  const handleCloseManageUserGroupsModal = () => {
    setUserError(null);
    setShowManageUserGroupsModal(false);
    setSelectedUser(null);
    // Invalidate userGroups query when closing the modal just in case (though mutation success also does this)
    queryClient.invalidateQueries({ queryKey: ["userGroups"] });
  };

  const handleSetUserGroups = async (
    userId: number,
    groupIds: UserGroupAssignInSchema[],
  ): Promise<void> => {
    setUserError(null);
    await updateUserGroupsMutation.mutateAsync({ userId, groupIds });
  };

  // --- Group Management Modal Handlers ---
  const handleShowCreateGroupModal = () => {
    setGroupError(null);
    setShowCreateGroupModal(true);
  };

  const handleCloseCreateGroupModal = () => {
    setGroupError(null);
    setShowCreateGroupModal(false);
  };

  const handleCreateGroup = async (groupData: GroupCreateInSchema): Promise<void> => {
    setGroupError(null);
    await createGroupMutation.mutateAsync(groupData);
  };

  const handleShowEditGroupModal = (group: GroupOutSchema) => {
    setGroupError(null);
    setSelectedGroup(group);
    setShowEditGroupModal(true);
  };

  const handleCloseEditGroupModal = () => {
    setGroupError(null);
    setShowEditGroupModal(false);
    setSelectedGroup(null);
  };

  const handleEditGroup = async (
    groupId: number,
    groupData: GroupUpdateInSchema,
  ): Promise<void> => {
    setGroupError(null);
    await updateGroupMutation.mutateAsync({ groupId, groupData });
  };

  const handleShowDeleteGroupModal = (group: GroupOutSchema) => {
    setGroupError(null);
    setSelectedGroup(group);
    setShowDeleteGroupModal(true);
  };

  const handleCloseDeleteGroupModal = () => {
    setGroupError(null);
    setShowDeleteGroupModal(false);
    setSelectedGroup(null);
  };

  // Simplified to rely on mutation's onError for error handling
  const handleDeleteGroup = async (groupId: number): Promise<void> => {
    setGroupError(null);
    await deleteGroupMutation.mutateAsync(groupId);
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
                    disabled={updateSystemSettingsMutation.isPending || !isDirty}
                  >
                    {updateSystemSettingsMutation.isPending ? (
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
          {userError && <Alert variant="danger">{userError}</Alert>}
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
          {groupError && <Alert variant="danger">{groupError}</Alert>}
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

      {/* --- User Management Modals --- */}
      <CreateUserModal
        show={showCreateUserModal}
        handleClose={handleCloseCreateUserModal}
        handleSave={handleCreateUser}
        loading={createUserMutation.isPending}
        error={userError}
      />

      <EditUserModal
        show={showEditUserModal}
        handleClose={handleCloseEditUserModal}
        handleSave={handleEditUser}
        user={selectedUser}
        loading={updateUserMutation.isPending}
        error={userError}
      />

      <ManageGroupsModal
        show={showManageUserGroupsModal}
        handleClose={handleCloseManageUserGroupsModal}
        handleSave={handleSetUserGroups}
        user={selectedUser}
        loading={updateUserGroupsMutation.isPending || userGroupsLoading}
        error={userError}
        allGroups={groups} // Pass the fetched groups to the user group management modal
        userGroupIds={userGroupIds}
      />

      {/* --- Group Management Modals --- */}
      <CreateGroupModal
        show={showCreateGroupModal}
        handleClose={handleCloseCreateGroupModal}
        handleSave={handleCreateGroup}
        loading={createGroupMutation.isPending}
        error={groupError}
      />

      {selectedGroup && (
        <EditGroupModal
          show={showEditGroupModal}
          handleClose={handleCloseEditGroupModal}
          handleSave={handleEditGroup}
          group={selectedGroup}
          loading={updateGroupMutation.isPending}
          error={groupError}
        />
      )}

      {selectedGroup && (
        <DeleteGroupModal
          show={showDeleteGroupModal}
          handleClose={handleCloseDeleteGroupModal}
          handleDelete={handleDeleteGroup}
          group={selectedGroup}
          loading={deleteGroupMutation.isPending}
          error={groupError}
        />
      )}
    </Container>
  );
};

export default SettingsPage;
