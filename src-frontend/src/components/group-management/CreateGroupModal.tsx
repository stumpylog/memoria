// src/components/group-management/CreateGroupModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { useForm } from "react-hook-form";

import { createGroupsMutation, listGroupsQueryKey } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface FormData {
  name: string;
}

interface CreateGroupModalProps {
  show: boolean;
  handleClose: () => void;
  onSuccess?: () => void;
}

const CreateGroupModal: React.FC<CreateGroupModalProps> = ({ show, handleClose, onSuccess }) => {
  const queryClient = useQueryClient();

  const {
    mutateAsync,
    isPending,
    error,
    reset: resetMutation,
  } = useMutation({
    ...createGroupsMutation(),
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
    formState: { errors, isDirty, isValid },
  } = useForm<FormData>({
    defaultValues: {
      name: "",
    },
    mode: "onChange",
  });

  useEffect(() => {
    if (show) {
      resetForm({ name: "" });
      resetMutation();
    }
  }, [show, resetForm, resetMutation]);

  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    await mutateAsync({ body: formData });
  };

  const errorMessage = getErrorMessage(error);

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Create New Group</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter group name"
              {...register("name", { required: "Group name cannot be empty" })}
              isInvalid={!!errors.name}
              disabled={isPending}
            />
            <Form.Control.Feedback type="invalid">{errors.name?.message}</Form.Control.Feedback>
          </Form.Group>
          <Button
            variant="primary"
            type="submit"
            disabled={isPending || !isDirty || !isValid}
            className="mt-3 w-100"
          >
            {isPending ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                {" Saving..."}
              </>
            ) : (
              "Save Group"
            )}
          </Button>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={isPending}>
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateGroupModal;
