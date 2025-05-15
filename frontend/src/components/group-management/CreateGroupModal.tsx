// src/components/group-management/CreateGroupModal.tsx
import React, { useState, useEffect } from "react";
import { Modal, Button, Form, Alert, Spinner } from "react-bootstrap";

import type { GroupCreateInSchema } from "../../api";

interface CreateGroupModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (groupData: GroupCreateInSchema) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const CreateGroupModal: React.FC<CreateGroupModalProps> = ({
  show,
  handleClose,
  handleSave,
  loading,
  error,
}) => {
  const [groupName, setGroupName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  // Reset state when modal is shown
  useEffect(() => {
    if (show) {
      setGroupName("");
      setLocalError(null);
    }
  }, [show]);

  const onSave = async () => {
    setLocalError(null); // Clear previous local errors
    if (!groupName.trim()) {
      setLocalError("Group name cannot be empty.");
      return;
    }

    const groupData: GroupCreateInSchema = { name: groupName };

    try {
      await handleSave(groupData);
      // handleSave's onSuccess should close the modal and invalidate queries
    } catch (err: any) {
      // Error is handled by the parent component's mutation onError,
      // but we catch here to prevent modal closing if handleSave throws
      // and the parent doesn't catch and re-throw.
      // For robustness, we can also display the parent error via the 'error' prop.
      console.error("Failed to save group:", err);
      // The parent 'error' prop will show the actual API error.
    }
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Create New Group</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {(localError || error) && <Alert variant="danger">{localError || error}</Alert>}
        <Form>
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter group name"
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
            "Save Group"
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateGroupModal;
