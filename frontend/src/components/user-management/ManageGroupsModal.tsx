// src/components/UserManagement/ManageGroupsModal.tsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Alert, ListGroup } from 'react-bootstrap';
import type { UserOutSchema, GroupOutSchema, GroupAssignSchema } from '../../api';

interface ManageGroupsModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userId: number, groupIds: GroupAssignSchema[]) => Promise<void>;
  user: UserOutSchema | null;
  loading: boolean;
  error: string | null;
  allGroups: GroupOutSchema[]; // List of all available groups
  userGroupIds: number[]; // List of IDs of groups the user is currently in
}

const ManageGroupsModal: React.FC<ManageGroupsModalProps> = ({
  show,
  handleClose,
  handleSave,
  user,
  loading,
  error,
  allGroups,
  userGroupIds,
}) => {
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([]);

  useEffect(() => {
    // Initialize selected groups when the modal opens or user changes
    setSelectedGroupIds(userGroupIds);
  }, [userGroupIds, user]);

  const handleGroupChange = (groupId: number, isChecked: boolean) => {
    setSelectedGroupIds(prevIds =>
      isChecked ? [...prevIds, groupId] : prevIds.filter(id => id !== groupId)
    );
  };

  const handleSubmit = async () => {
    if (!user) return;
    const groupAssignments: GroupAssignSchema[] = selectedGroupIds.map(id => ({ id }));
    await handleSave(user.id, groupAssignments);
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Manage Groups for {user?.username}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form>
          <Form.Label>Select Groups</Form.Label>
          <ListGroup style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {allGroups.map(group => (
              <ListGroup.Item key={group.id}>
                <Form.Check
                  type="checkbox"
                  label={group.name}
                  checked={selectedGroupIds.includes(group.id)}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    handleGroupChange(group.id, e.target.checked)
                  }
                />
              </ListGroup.Item>
            ))}
            {allGroups.length === 0 && <ListGroup.Item>No groups available.</ListGroup.Item>}
          </ListGroup>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Close
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ManageGroupsModal;
