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
  UserGroupAssignInSchema,
  UserInCreateSchemaWritable,
  GroupOutSchema,
  GroupCreateInSchema,
  GroupUpdateInSchema,
} from "../api";

// Components
import CreateUserModal from "../components/user-management/CreateUserModal";
import EditUserModal from "../components/user-management/EditUserModal";
import ManageGroupsModal from "../components/user-management/ManageGroupsModal"; // This is for user group assignment
// We will need new modals for group management:
import CreateGroupModal from "../components/group-management/CreateGroupModal"; // Placeholder - need to create
import EditGroupModal from "../components/group-management/EditGroupModal"; // Placeholder - need to create
import DeleteGroupModal from "../components/group-management/DeleteGroupModal"; // Placeholder - need to create

// API functions
import {
  userGetAll,
  groupGetAll, // Already exists and used
  userCreate,
  userSetInfo,
  userSetGroups,
  userGetGroups,
  // New API functions for group management
  groupsCreate, // Assuming this function exists
  groupDeleteSingle, // Assuming this function exists
  groupUpdateSingle, // Assuming this function exists
  // groupGetSingle, // Not strictly needed for this implementation but available
} from "../api";

const SettingsPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  // --- User Management State ---
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showManageUserGroupsModal, setShowManageUserGroupsModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserOutSchema | null>(null);
  const [userError, setUserError] = useState<string | null>(null); // Dedicated user error state

  // --- Group Management State ---
  const [showCreateGroupModal, setShowCreateGroupModal] = useState(false);
  const [showEditGroupModal, setShowEditGroupModal] = useState(false);
  const [showDeleteGroupModal, setShowDeleteGroupModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<GroupOutSchema | null>(null);
  const [groupError, setGroupError] = useState<string | null>(null); // Dedicated group error state

  // --- User Management Queries ---
  const {
    data: users = [],
    isLoading: usersLoading,
    error: usersQueryError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: async () => {
      const response = await userGetAll();
      return response?.data || [];
    },
  });

  const { data: userGroupIds = [], isLoading: userGroupsLoading } = useQuery({
    queryKey: ["userGroups", selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return [];
      const response = await userGetGroups({ path: { user_id: selectedUser.id } });
      // Assuming the response data is an array of group objects with an 'id' property
      return response?.data?.map((group) => group.id) || [];
    },
    enabled: !!selectedUser && showManageUserGroupsModal, // Only run when a user is selected and the modal is open
  });

  // --- Group Management Queries ---
  const {
    data: groups = [], // Renamed from allGroups for clarity in this section
    isLoading: groupsLoading,
    error: groupsQueryError,
  } = useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      const response = await groupGetAll();
      return response?.data || [];
    },
  });

  // --- User Management Mutations ---
  const createUserMutation = useMutation({
    mutationFn: (userData: UserInCreateSchemaWritable) => userCreate({ body: userData }),
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
      userSetInfo({ path: { user_id: userId }, body: userData }),
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
      userSetGroups({ path: { user_id: userId }, body: groupIds }),
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
    mutationFn: (groupData: GroupCreateInSchema) => groupsCreate({ body: groupData }),
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
      groupUpdateSingle({ path: { group_id: groupId }, body: groupData }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      handleCloseEditGroupModal();
    },
    onError: (err: any) => {
      setGroupError(err.message || `Failed to update group.`);
    },
  });

  const deleteGroupMutation = useMutation({
    mutationFn: (groupId: number) => groupDeleteSingle({ path: { group_id: groupId } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      handleCloseDeleteGroupModal();
    },
    onError: (err: any) => {
      setGroupError(err.message || `Failed to delete group.`);
    },
  });

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
                    <td colSpan={9} className="text-center">
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

      {/* --- Group Management Modals (Placeholders) --- */}
      {/* You will need to create these components */}
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
