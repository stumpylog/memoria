// src/components/group-management/EditGroupModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Form } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { GroupOutSchema } from "../../api";

import { listGroupsQueryKey, updateGroupMutation } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";
import FormModal from "../common/FormModal";

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

  const form = useForm<FormValues>({
    defaultValues: {
      name: "",
    },
    mode: "onChange",
  });

  const {
    register,
    reset: resetForm,
    formState: { errors },
  } = form;

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
    <FormModal
      show={show}
      onHide={handleClose}
      title={`Edit Group: ${group.name}`}
      isLoading={isPending}
      error={errorMessage}
      form={form}
      onSubmit={onSubmit}
    >
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
    </FormModal>
  );
};

export default EditGroupModal;
