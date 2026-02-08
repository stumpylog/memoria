// src/components/group-management/CreateGroupModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Form } from "react-bootstrap";
import { useForm } from "react-hook-form";

import { createGroupsMutation, listGroupsQueryKey } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";
import FormModal from "../common/FormModal";

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

  const form = useForm<FormData>({
    defaultValues: {
      name: "",
    },
    mode: "onChange",
  });

  const { register, formState } = form;
  const { errors } = formState;

  useEffect(() => {
    if (show) {
      form.reset({ name: "" });
      resetMutation();
    }
  }, [show, form, resetMutation]);

  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    await mutateAsync({ body: formData });
  };

  const errorMessage = getErrorMessage(error);

  return (
    <FormModal
      show={show}
      onHide={handleClose}
      title="Create New Group"
      isLoading={isPending}
      error={errorMessage}
      form={form}
      onSubmit={onSubmit}
      submitLabel="Save Group"
    >
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
    </FormModal>
  );
};

export default CreateGroupModal;
