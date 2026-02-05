// src/components/group-management/DeleteGroupModal.tsx
import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Modal, Spinner } from "react-bootstrap";

import type { GroupOutSchema } from "../../api";

import { deleteGroupMutation, listGroupsQueryKey } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface DeleteGroupModalProps {
  show: boolean;
  handleClose: () => void;
  group: GroupOutSchema;
  onSuccess?: () => void;
}

const DeleteGroupModal: React.FC<DeleteGroupModalProps> = ({
  show,
  handleClose,
  group,
  onSuccess,
}) => {
  const queryClient = useQueryClient();

  const {
    mutateAsync,
    isPending,
    error,
    reset: resetMutation,
  } = useMutation({
    ...deleteGroupMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listGroupsQueryKey() });
      onSuccess?.();
      handleClose();
    },
  });

  useEffect(() => {
    if (show) {
      resetMutation();
    }
  }, [show, resetMutation]);

  const onDelete = async () => {
    await mutateAsync({ path: { group_id: group.id } });
  };

  const errorMessage = getErrorMessage(error);

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Confirm Group Deletion</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <p>
          Are you sure you want to delete the group "<strong>{group.name}</strong>"? This action
          cannot be undone.
        </p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={isPending}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onDelete} disabled={isPending}>
          {isPending ? (
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
