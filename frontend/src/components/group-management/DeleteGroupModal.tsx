// src/components/group-management/DeleteGroupModal.tsx
import React, { useEffect } from "react";
import { Alert, Button, Modal, Spinner } from "react-bootstrap";

import type { GroupOutSchema } from "../../api";

interface DeleteGroupModalProps {
  show: boolean;
  handleClose: () => void;
  handleDelete: (groupId: number) => Promise<void>;
  group: GroupOutSchema | null; // The group being deleted
  loading: boolean;
  error: string | null;
}

const DeleteGroupModal: React.FC<DeleteGroupModalProps> = ({
  show,
  handleClose,
  handleDelete,
  group,
  loading,
  error,
}) => {
  // Clear error when modal is shown
  useEffect(() => {
    if (show) {
      // Clear any previous errors when the modal opens
    }
  }, [show]);

  const onDelete = async () => {
    if (!group) return; // Should not happen if modal is shown

    await handleDelete(group.id);
  };

  // Don't render if no group is selected (though parent handles this with conditional rendering)
  if (!group && show) {
    return null;
  }

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Confirm Group Deletion</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <p>
          Are you sure you want to delete the group "<strong>{group?.name}</strong>"? This action
          cannot be undone.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onDelete} disabled={loading}>
          {loading ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              {" Deleting..."}
            </>
          ) : (
            "Delete Group"
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default DeleteGroupModal;
