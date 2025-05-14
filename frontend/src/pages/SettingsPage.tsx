// src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react';
import { Container, Card, Alert, Button, Table, Spinner } from 'react-bootstrap';
import { useAuth } from '../hooks/useAuth';
import { Navigate } from 'react-router-dom';
// Assuming these types are correctly defined in '../api' or linked files
import type { UserOutSchema, UserUpdateInSchemeWritable, GroupOutSchema, GroupAssignSchema, UserInCreateSchemaWritable } from '../api';
import CreateUserModal from '../components/user-management/CreateUserModal';
import EditUserModal from '../components/user-management/EditUserModal';
import ManageGroupsModal from '../components/user-management/ManageGroupsModal';
// Assuming these functions are correctly implemented in '../api'
import { userGetAll, groupGetAll, userCreate, userSetInfo, userSetGroups, userGetGroups } from '../api';


const SettingsPage: React.FC = () => {
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState<UserOutSchema[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State for Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showGroupsModal, setShowGroupsModal] = useState(false);

  const [selectedUser, setSelectedUser] = useState<UserOutSchema | null>(null);
  const [allGroups, setAllGroups] = useState<GroupOutSchema[]>([]);
  const [userGroupIds, setUserGroupIds] = useState<number[]>([]);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const userList = await userGetAll();
      // Safely access data property
      if (userList && userList.data) {
        setUsers(userList.data);
      } else {
          // Handle case where response or data is unexpectedly null/undefined
          console.error("Failed to fetch users: Data is missing from response.");
          setError("Failed to load users: Received invalid data.");
          setUsers([]); // Set to empty array on invalid data
      }
    } catch (err) {
      console.error("Failed to fetch users:", err);
      setError("Failed to load users.");
      setUsers([]); // Set to empty array on error
    } finally {
      setLoading(false);
    }
  };

  const fetchAllGroups = async () => {
      try {
          const groups = await groupGetAll();
          // Safely access data property
          if (groups && groups.data) {
             setAllGroups(groups.data);
          } else {
              console.error("Failed to fetch all groups: Data is missing from response.");
              // Decide how to handle this - maybe show an error in the groups modal later
              setAllGroups([]); // Set to empty array on invalid data
          }
      } catch (err) {
           console.error("Failed to fetch all groups:", err);
           // Decide how to handle this error
           setAllGroups([]); // Set to empty array on error
      }
  }

   useEffect(() => {
       // Fetch users and groups when the component mounts
       fetchUsers();
       fetchAllGroups();
   }, []);


  // --- Create User Handlers ---
  const handleShowCreateModal = () => setShowCreateModal(true);
  const handleCloseCreateModal = () => {
       // Clear modal-specific error when closing
      setError(null);
      setShowCreateModal(false);
      // Reset form state in the modal component via its own state
  }
   // Note: Assuming UserInCreateSchemaWritable is compatible with what the CreateUserModal form provides (UserUpdateInSchemeWritable)
  const handleCreateUser = async (userData: UserInCreateSchemaWritable) => {
      // Use a separate loading state for modals if multiple API calls can happen concurrently
      // For simplicity, reusing page loading state here, but consider modalLoading:
      // const [modalLoading, setModalLoading] = useState(false);
      // setModalLoading(true);
      setLoading(true);
      setError(null); // Clear any previous errors before new attempt
      try {
          const newUserResponse = await userCreate({body: userData});
          // Safely access data property
           if (newUserResponse && newUserResponse.data) {
               setUsers([...users, newUserResponse.data]); // Add the new user to the list
               handleCloseCreateModal(); // Close modal on success
           } else {
                console.error("Failed to create user: Data is missing from response.");
                setError("Failed to create user: Received invalid data.");
           }
      } catch (err: any) { // Catch error to display in modal
          console.error("Failed to create user:", err);
           setError(err.message || "Failed to create user.");
      } finally {
          // setModalLoading(false);
           setLoading(false);
      }
  };

  // --- Edit User Handlers ---
  const handleShowEditModal = (user: UserOutSchema) => {
       // Clear modal-specific error before opening
      setError(null);
      setSelectedUser(user);
      setShowEditModal(true);
  };
  const handleCloseEditModal = () => {
      setShowEditModal(false);
      setSelectedUser(null); // Clear selected user
      setError(null); // Clear any previous errors
  };
   const handleEditUser = async (userId: number, userData: Partial<UserUpdateInSchemeWritable>) => {
      // Use modal loading state
      setLoading(true);
      setError(null); // Clear any previous errors
      try {
          const updatedUserResponse = await userSetInfo({path: {user_id: userId}, body: userData});
          // Safely access data property
           if (updatedUserResponse && updatedUserResponse.data) {
               // Update the user in the local state
               setUsers(users.map(user => user.id === userId ? updatedUserResponse.data : user));
               handleCloseEditModal(); // Close modal on success
           } else {
               console.error(`Failed to update user ${userId}: Data is missing from response.`);
               setError(`Failed to update user ${userId}: Received invalid data.`);
           }
      } catch (err: any) {
           console.error(`Failed to update user ${userId}:`, err);
           setError(err.message || `Failed to update user ${userId}.`);
      } finally {
           setLoading(false);
      }
   };

  // --- Manage Groups Handlers ---
  const handleShowGroupsModal = async (user: UserOutSchema) => {
       // Clear modal-specific error before opening
       setError(null);
      setSelectedUser(user);
      setShowGroupsModal(true);
      // Fetch user's current groups when opening the modal
      try {
          const userGroupsResponse = await userGetGroups({path: {user_id: user.id}});
          // Safely access data property
           if (userGroupsResponse && userGroupsResponse.data) {
               setUserGroupIds(userGroupsResponse.data.map(group => group.id));
           } else {
               console.error(`Failed to fetch groups for user ${user.id}: Data is missing from response.`);
               setError(`Failed to load groups for user ${user.id}: Received invalid data.`);
               setUserGroupIds([]); // Clear groups on invalid data
           }
      } catch (err: any) {
          console.error(`Failed to fetch groups for user ${user.id}:`, err);
          setError(err.message || `Failed to load groups for user ${user.id}.`);
          setUserGroupIds([]); // Clear groups on error
      }
      // Note: loading state for groups modal fetch is handled implicitly here,
      // might want explicit state if this fetch is long or independent.
  };
  const handleCloseGroupsModal = () => {
      setShowGroupsModal(false);
      setSelectedUser(null); // Clear selected user
      setUserGroupIds([]); // Clear user groups
      setError(null); // Clear any previous errors
  };
  const handleSetUserGroups = async (userId: number, groupIds: GroupAssignSchema[]) => {
      // Use modal loading state
      setLoading(true);
      setError(null); // Clear any previous errors
      try {
           // userSetGroups might return something or just a status,
           // assuming it succeeds if no error is thrown.
          await userSetGroups({path: {user_id: userId}, body: groupIds});
          // Re-fetch users to potentially update group info display if needed (optional)
          // If user group display is critical to be immediately accurate on the table,
           // uncommenting fetchUsers() here would update the table, but adds another API call.
           // fetchUsers();
          handleCloseGroupsModal(); // Close modal on success
      } catch (err: any) {
           console.error(`Failed to set user groups for user ${userId}:`, err);
           setError(err.message || `Failed to update user groups for user ${userId}.`);
      } finally {
           setLoading(false);
      }
  };


  // This check can also be part of ProtectedRoute if settings becomes a common protected resource type
  if (currentUser === undefined) {
      // Handle loading state for auth user if needed
      return <Spinner animation="border" />; // Or a loading message
  }

  if (currentUser === null || (!currentUser.is_staff && !currentUser.is_superuser)) {
    return <Navigate to="/" replace />; // Or to an "Unauthorized" page
  }

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

          {loading && !users.length && !error ? ( // Show spinner only on initial load if no users fetched and no error
              <div className="d-flex justify-content-center">
                  <Spinner animation="border" role="status">
                      <span className="visually-hidden">Loading Users...</span>
                  </Spinner>
              </div>
          ) : error ? (
            <Alert variant="danger">{error}</Alert>
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
                    {/* Handle potentially null/undefined boolean values gracefully */}
                    <td>{user.is_active ?? true ? 'Yes' : 'No'}</td> {/* Assuming default active is true */}
                    <td>{user.is_staff ?? false ? 'Yes' : 'No'}</td> {/* Assuming default staff is false */}
                    <td>{user.is_superuser ?? false ? 'Yes' : 'No'}</td> {/* Assuming default superuser is false */}
                    <td>
                      {/* Ensure user is staff/superuser before showing edit/groups buttons */}
                       {(currentUser.is_staff || currentUser.is_superuser) && (
                           <>
                                <Button variant="secondary" size="sm" className="me-2" onClick={() => handleShowEditModal(user)}>
                                    Edit
                                </Button>
                                <Button variant="info" size="sm" onClick={() => handleShowGroupsModal(user)}>
                                    Groups
                                </Button>
                                {/* Add delete button here if needed */}
                           </>
                       )}
                    </td>
                  </tr>
                ))}
                 {users.length === 0 && !loading && !error && <tr><td colSpan={9} className="text-center">No users found.</td></tr>}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      {/* Modals */}
      {/* Pass down error state to modals for display within the modal body */}
      <CreateUserModal
        show={showCreateModal}
        handleClose={handleCloseCreateModal}
        handleSave={handleCreateUser}
        loading={loading} // Consider separate loading state for modals
        error={error} // Pass error state
      />

      <EditUserModal
        show={showEditModal}
        handleClose={handleCloseEditModal}
        handleSave={handleEditUser}
        user={selectedUser}
        loading={loading} // Consider separate loading state for modals
        error={error} // Pass error state
      />

       <ManageGroupsModal
          show={showGroupsModal}
          handleClose={handleCloseGroupsModal}
          handleSave={handleSetUserGroups}
          user={selectedUser}
          loading={loading} // Consider separate loading state for modals
          error={error} // Pass error state
          allGroups={allGroups}
          userGroupIds={userGroupIds}
       />

    </Container>
  );
};

export default SettingsPage;
