// src/components/group-management/EditGroupModal.tsx
import React, { useState, useEffect } from "react";
import { Modal, Button, Form, Alert, Spinner } from "react-bootstrap";

// Assuming GroupOutSchema and GroupUpdateInSchema types exist in your api types
import type { GroupOutSchema, GroupUpdateInSchema } from "../../api";

interface EditGroupModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (groupId: number, groupData: GroupUpdateInSchema) => Promise<void>;
  group: GroupOutSchema | null; // The group being edited
  loading: boolean;
  error: string | null;
}

const EditGroupModal: React.FC<EditGroupModalProps> = ({
  show,
  handleClose,
  handleSave,
  group,
  loading,
  error,
}) => {
  const [groupName, setGroupName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  // Populate form when modal is shown or selected group changes
  useEffect(() => {
    if (show && group) {
      setGroupName(group.name);
      setLocalError(null); // Clear local errors on show
    } else if (!show) {
      // Reset state when modal is closed
      setGroupName("");
      setLocalError(null);
    }
  }, [show, group]);

  const onSave = async () => {
    setLocalError(null); // Clear previous local errors
    if (!group) return; // Should not happen if modal is shown, but good practice

    if (!groupName.trim()) {
      setLocalError("Group name cannot be empty.");
      return;
    }

    const groupData: GroupUpdateInSchema = { name: groupName };

    try {
      await handleSave(group.id, groupData);
      // handleSave's onSuccess should close the modal and invalidate queries
    } catch (err: any) {
      // Error is handled by the parent component's mutation onError
      console.error("Failed to update group:", err);
      // The parent 'error' prop will show the actual API error.
    }
  };

  // Don't render if no group is selected (though parent handles this with conditional rendering)
  if (!group && show) {
    return null;
  }

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Group: {group?.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {(localError || error) && <Alert variant="danger">{localError || error}</Alert>}
        <Form>
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter new group name"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              isInvalid={!!localError}
              disabled={loading}
            />
            <Form.Control.Feedback type="invalid">{localError}</Form.Control.Feedback>
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="primary" onClick={onSave} disabled={loading}>
          {loading ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              {" Saving..."}
            </>
          ) : (
            "Save Changes"
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default EditGroupModal;
