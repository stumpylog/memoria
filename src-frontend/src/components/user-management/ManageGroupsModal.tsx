// src/components/UserManagement/ManageGroupsModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect, useMemo } from "react";
import { Form, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { GroupOutSchema, UserGroupAssignInSchema, UserOutSchema } from "../../api";

import {
  usersGroupsListQueryKey,
  usersGroupsUpdateMutation,
  usersListQueryKey,
} from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";
import FormModal from "../common/FormModal";
import ThemedSelect from "../common/ThemedSelect";

interface GroupOption {
  value: number;
  label: string;
}

interface FormData {
  selectedGroups: GroupOption[];
}

interface ManageGroupsModalProps {
  show: boolean;
  handleClose: () => void;
  user: UserOutSchema;
  allGroups: GroupOutSchema[];
  userGroupIds: number[];
  userGroupsLoading: boolean;
  onSuccess?: () => void;
}

const ManageGroupsModal: React.FC<ManageGroupsModalProps> = ({
  show,
  handleClose,
  user,
  allGroups,
  userGroupIds,
  userGroupsLoading,
  onSuccess,
}) => {
  const queryClient = useQueryClient();

  const {
    mutateAsync,
    isPending,
    error,
    reset: resetMutation,
  } = useMutation({
    ...usersGroupsUpdateMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: usersListQueryKey() });
      queryClient.invalidateQueries({
        queryKey: usersGroupsListQueryKey({ path: { user_id: user.id } }),
      });
      onSuccess?.();
      handleClose();
    },
  });

  const form = useForm<FormData>({
    defaultValues: {
      selectedGroups: [],
    },
  });

  const { control } = form;

  const groupOptions: GroupOption[] = useMemo(
    () =>
      allGroups.map((group) => ({
        value: group.id,
        label: group.name,
      })),
    [allGroups],
  );

  const selectedGroupOptions: GroupOption[] = useMemo(
    () => groupOptions.filter((option) => userGroupIds.includes(option.value)),
    [groupOptions, userGroupIds],
  );

  useEffect(() => {
    if (show && user) {
      form.reset({ selectedGroups: selectedGroupOptions });
      resetMutation();
    }
  }, [show, user, selectedGroupOptions, form, resetMutation]);

  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    const groupAssignments: UserGroupAssignInSchema[] = formData.selectedGroups.map((option) => ({
      id: option.value,
    }));

    await mutateAsync({
      path: { user_id: user.id },
      body: groupAssignments,
    });
  };

  const errorMessage = getErrorMessage(error);
  const isLoading = isPending || userGroupsLoading;

  if (userGroupsLoading) {
    return (
      <FormModal
        show={show}
        onHide={handleClose}
        title={`Manage Groups for ${user.username}`}
        size="lg"
        isLoading={false}
        error={null}
        form={form}
        onSubmit={onSubmit}
      >
        <div className="d-flex justify-content-center py-4">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading groups...</span>
          </Spinner>
        </div>
      </FormModal>
    );
  }

  return (
    <FormModal
      show={show}
      onHide={handleClose}
      title={`Manage Groups for ${user.username}`}
      size="lg"
      isLoading={isPending}
      error={errorMessage}
      form={form}
      onSubmit={onSubmit}
    >
      <Form.Group className="mb-3">
        <Form.Label>Select Groups</Form.Label>
        <Controller
          name="selectedGroups"
          control={control}
          render={({ field }) => (
            <ThemedSelect
              {...field}
              isMulti
              options={groupOptions}
              placeholder="Search and select groups..."
              isClearable
              isSearchable
              closeMenuOnSelect={false}
              noOptionsMessage={({ inputValue }) =>
                inputValue ? `No groups found matching "${inputValue}"` : "No groups available"
              }
              isDisabled={groupOptions.length === 0 || isPending}
            />
          )}
        />
        {groupOptions.length === 0 && (
          <Form.Text className="text-muted">No groups are available to assign.</Form.Text>
        )}
      </Form.Group>
    </FormModal>
  );
};

export default ManageGroupsModal;
