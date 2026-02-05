// src/components/group-management/EditGroupModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { GroupOutSchema } from "../../api";

import { listGroupsQueryKey, updateGroupMutation } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface FormValues {
  name: string;
}

interface EditGroupModalProps {
  show: boolean;
  handleClose: () => void;
  group: GroupOutSchema;
  onSuccess?: () => void;
}

const EditGroupModal: React.FC<EditGroupModalProps> = ({
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
    ...updateGroupMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listGroupsQueryKey() });
      onSuccess?.();
      handleClose();
    },
  });

  const {
    register,
    handleSubmit,
    reset: resetForm,
    formState: { errors, isDirty },
  } = useForm<FormValues>({
    defaultValues: {
      name: "",
    },
    mode: "onChange",
  });

  useEffect(() => {
    if (show && group) {
      resetForm({ name: group.name });
      resetMutation();
    }
  }, [show, group, resetForm, resetMutation]);

  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    await mutateAsync({
      path: { group_id: group.id },
      body: { name: data.name },
    });
  };

  const errorMessage = getErrorMessage(error);

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Group: {group.name}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter new group name"
              {...register("name", { required: "Group name cannot be empty." })}
              isInvalid={!!errors.name}
              disabled={isPending}
            />
            <Form.Control.Feedback type="invalid">{errors.name?.message}</Form.Control.Feedback>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose} disabled={isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isPending || !isDirty || !!errors.name}
          >
            {isPending ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                {" Saving..."}
              </>
            ) : (
              "Save Changes"
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default EditGroupModal;
