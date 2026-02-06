// src/components/image/GroupPermissionsModal.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type {
  GroupSchemaOut,
  ImageMetadataSchemaOut,
  ImageMetadataUpdateSchemaIn,
} from "../../api";

import {
  imageUpdateMetadataMutation,
  listGroupsOptions,
} from "../../api/@tanstack/react-query.gen";
import ThemedSelect from "../common/ThemedSelect";

interface GroupPermissionsModalProps {
  show: boolean;
  onHide: () => void;
  imageId: number;
  currentMetadata: ImageMetadataSchemaOut;
  onPermissionsUpdated: () => void;
}

interface FormData {
  view_group_ids: number[];
  edit_group_ids: number[];
}

const GroupPermissionsModal: React.FC<GroupPermissionsModalProps> = ({
  show,
  onHide,
  imageId,
  currentMetadata,
  onPermissionsUpdated,
}) => {
  const queryClient = useQueryClient();

  const { data: groupsResponse, isLoading: groupsLoading } = useQuery({
    ...listGroupsOptions(),
    enabled: show,
  });

  const groups: GroupSchemaOut[] = groupsResponse ?? [];

  const {
    control,
    handleSubmit,
    formState: { isSubmitting },
    reset,
  } = useForm<FormData>({
    defaultValues: {
      view_group_ids: currentMetadata?.view_groups?.map((g) => g.id) || [],
      edit_group_ids: currentMetadata?.edit_groups?.map((g) => g.id) || [],
    },
  });

  React.useEffect(() => {
    if (show) {
      reset({
        view_group_ids: currentMetadata?.view_groups?.map((g) => g.id) || [],
        edit_group_ids: currentMetadata?.edit_groups?.map((g) => g.id) || [],
      });
    }
  }, [reset, show, currentMetadata]);

  const updatePermissionsMutation = useMutation({
    ...imageUpdateMetadataMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metadata", imageId] });
      onHide();
      onPermissionsUpdated();
    },
    onError: (err) => {
      console.error("Failed to update permissions:", err);
    },
  });

  const onSubmit = (data: FormData) => {
    const updateData: ImageMetadataUpdateSchemaIn = {
      title: currentMetadata.title,
      description: currentMetadata.description,
      view_group_ids: data.view_group_ids,
      edit_group_ids: data.edit_group_ids,
    };
    updatePermissionsMutation.mutate({
      path: { image_id: imageId },
      body: updateData,
    });
  };

  // Prepare options for react-select - Convert value to string
  const groupOptions = groups.map((group) => ({
    value: String(group.id), // Convert number to string here
    label: group.name,
  }));

  if (groupsLoading) {
    return (
      <Modal show={show} onHide={onHide} centered>
        <Modal.Header closeButton>
          <Modal.Title>Edit Permissions</Modal.Title>
        </Modal.Header>
        <Modal.Body className="text-center">
          <Spinner animation="border" />
          <p className="mt-2">Loading groups...</p>
        </Modal.Body>
      </Modal>
    );
  }

  return (
    <Modal show={show} onHide={onHide} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Edit Image Permissions</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {updatePermissionsMutation.isError && (
            <div className="alert alert-danger">
              Failed to update permissions. Please try again.
            </div>
          )}

          {/* View Permissions */}
          <div className="mb-4">
            <h6>View Permissions</h6>
            <p className="text-muted small">Select groups that can view this image.</p>
            <Controller
              name="view_group_ids"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  {...field}
                  isMulti
                  options={groupOptions}
                  // getOptionValue is now implicitly handled by the type of groupOptions
                  getOptionLabel={(option) => option.label}
                  value={groupOptions.filter((option) =>
                    // Compare string values
                    field.value.map(String).includes(option.value),
                  )}
                  onChange={(selectedOptions) =>
                    // Convert back to number before passing to react-hook-form
                    field.onChange(selectedOptions.map((option) => Number(option.value)))
                  }
                />
              )}
            />
          </div>

          {/* Edit Permissions */}
          <div className="mb-3">
            <h6>Edit Permissions</h6>
            <p className="text-muted small">Select groups that can edit this image.</p>
            <Controller
              name="edit_group_ids"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  {...field}
                  isMulti
                  options={groupOptions}
                  // getOptionValue is now implicitly handled by the type of groupOptions
                  getOptionLabel={(option) => option.label}
                  value={groupOptions.filter((option) =>
                    // Compare string values
                    field.value.map(String).includes(option.value),
                  )}
                  onChange={(selectedOptions) =>
                    // Convert back to number before passing to react-hook-form
                    field.onChange(selectedOptions.map((option) => Number(option.value)))
                  }
                />
              )}
            />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isSubmitting || updatePermissionsMutation.isPending}
          >
            {isSubmitting || updatePermissionsMutation.isPending
              ? "Saving..."
              : "Save Permissions"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default GroupPermissionsModal;
