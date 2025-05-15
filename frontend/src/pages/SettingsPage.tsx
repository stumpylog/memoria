// src/pages/SettingsPage.tsx
import React, { useState } from "react";
import { Container, Card, Alert, Button, Table, Spinner } from "react-bootstrap";
import { useAuth } from "../hooks/useAuth";
import { Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
// Types
import type {
  UserOutSchema,
  UserUpdateInSchemeWritable,
  GroupAssignSchema,
  UserInCreateSchemaWritable,
} from "../api";
// Components
import CreateUserModal from "../components/user-management/CreateUserModal";
import EditUserModal from "../components/user-management/EditUserModal";
import ManageGroupsModal from "../components/user-management/ManageGroupsModal";
// API functions
import {
  userGetAll,
  groupGetAll,
  userCreate,
  userSetInfo,
  userSetGroups,
  userGetGroups,
} from "../api";

const SettingsPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showGroupsModal, setShowGroupsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserOutSchema | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Queries
  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const response = await userGetAll();
      return response?.data || [];
    },
  });

  const { data: allGroups = [] } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      const response = await groupGetAll();
      return response?.data || [];
    },
  });

  const { data: userGroupIds = [], isLoading: userGroupsLoading } = useQuery({
    queryKey: ["userGroups", selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return [];
      const response = await userGetGroups({ path: { user_id: selectedUser.id } });
      return response?.data?.map((group) => group.id) || [];
    },
    enabled: !!selectedUser && showGroupsModal,
  });

  // Mutations
  const createUserMutation = useMutation({
    mutationFn: (userData: UserInCreateSchemaWritable) => userCreate({ body: userData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      handleCloseCreateModal();
    },
    onError: (err: any) => {
      setError(err.message || "Failed to create user.");
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, userData }: { userId: number; userData: UserUpdateInSchemeWritable }) =>
      userSetInfo({ path: { user_id: userId }, body: userData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      handleCloseEditModal();
    },
    onError: (err: any) => {
      setError(err.message || `Failed to update user.`);
    },
  });

  const updateUserGroupsMutation = useMutation({
    mutationFn: ({ userId, groupIds }: { userId: number; groupIds: GroupAssignSchema[] }) =>
      userSetGroups({ path: { user_id: userId }, body: groupIds }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["userGroups"] });
      handleCloseGroupsModal();
    },
    onError: (err: any) => {
      setError(err.message || `Failed to update user groups.`);
    },
  });

  // Modal handlers
  const handleShowCreateModal = () => {
    setError(null);
    setShowCreateModal(true);
  };

  const handleCloseCreateModal = () => {
    setError(null);
    setShowCreateModal(false);
  };

  const handleCreateUser = (userData: UserInCreateSchemaWritable): Promise<void> => {
    setError(null);
    return createUserMutation
      .mutateAsync(userData)
      .then(() => {})
      .catch((error) => {
        throw error;
      });
  };

  const handleShowEditModal = (user: UserOutSchema) => {
    setError(null);
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setError(null);
    setShowEditModal(false);
    setSelectedUser(null);
  };

  const handleEditUser = (userId: number, userData: UserUpdateInSchemeWritable): Promise<void> => {
    setError(null);
    return updateUserMutation
      .mutateAsync({ userId, userData })
      .then(() => {})
      .catch((error) => {
        throw error;
      });
  };

  const handleShowGroupsModal = (user: UserOutSchema) => {
    setError(null);
    setSelectedUser(user);
    setShowGroupsModal(true);
  };

  const handleCloseGroupsModal = () => {
    setError(null);
    setShowGroupsModal(false);
    setSelectedUser(null);
  };

  const handleSetUserGroups = (userId: number, groupIds: GroupAssignSchema[]): Promise<void> => {
    setError(null);
    return updateUserGroupsMutation
      .mutateAsync({ userId, groupIds })
      .then(() => {})
      .catch((error) => {
        throw error;
      });
  };

  // Auth check
  if (currentUser === undefined) {
    return <Spinner animation="border" />;
  }

  if (currentUser === null || (!currentUser.is_staff && !currentUser.is_superuser)) {
    return <Navigate to="/" replace />;
  }

  // Determine if there's an error to display
  const displayError =
    error ||
    (usersError instanceof Error
      ? usersError.message
      : usersError
        ? "Failed to load users."
        : null);

  return (
    <Container fluid className="p-4">
      <Card>
        <Card.Header as="h2">Application Settings</Card.Header>
        <Card.Body>
          <Alert variant="info">This page is available to staff and superusers only.</Alert>

          <h3>User Management</h3>
          <Button variant="primary" onClick={handleShowCreateModal} className="mb-3">
            Create New User
          </Button>

          {usersLoading && !users.length ? (
            <div className="d-flex justify-content-center">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading Users...</span>
              </Spinner>
            </div>
          ) : displayError ? (
            <Alert variant="danger">{displayError}</Alert>
          ) : (
            <Table striped bordered hover responsive>
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
                    <td>
                      {(currentUser.is_staff || currentUser.is_superuser) && (
                        <>
                          <Button
                            variant="secondary"
                            size="sm"
                            className="me-2"
                            onClick={() => handleShowEditModal(user)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="info"
                            size="sm"
                            onClick={() => handleShowGroupsModal(user)}
                          >
                            Groups
                          </Button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
                {users.length === 0 && !usersLoading && !displayError && (
                  <tr>
                    <td colSpan={9} className="text-center">
                      No users found.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Modals */}
      <CreateUserModal
        show={showCreateModal}
        handleClose={handleCloseCreateModal}
        handleSave={handleCreateUser}
        loading={createUserMutation.isPending}
        error={error}
      />

      <EditUserModal
        show={showEditModal}
        handleClose={handleCloseEditModal}
        handleSave={handleEditUser}
        user={selectedUser}
        loading={updateUserMutation.isPending}
        error={error}
      />

      <ManageGroupsModal
        show={showGroupsModal}
        handleClose={handleCloseGroupsModal}
        handleSave={handleSetUserGroups}
        user={selectedUser}
        loading={updateUserGroupsMutation.isPending || userGroupsLoading}
        error={error}
        allGroups={allGroups}
        userGroupIds={userGroupIds}
      />
    </Container>
  );
};

export default SettingsPage;
