// src/components/EditFolderModal.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { FolderDetailSchemaOut, FolderUpdateSchemaIn, GroupSchemaOut } from "../../api";

import { listGroups, updateFolderInfo } from "../../api";
import ThemedSelect from "../common/ThemedSelect";

interface EditFolderModalProps {
  show: boolean;
  handleClose: () => void;
  folder: FolderDetailSchemaOut;
  onSaveSuccess: () => void; // No need to pass updated folder back if not redirecting
}

// Define form data type, adding group IDs
interface EditFolderFormData {
  name: string;
  description: string | null;
  view_group_ids: number[];
  edit_group_ids: number[];
}

const EditFolderModal: React.FC<EditFolderModalProps> = ({
  show,
  handleClose,
  folder,
  onSaveSuccess,
}) => {
  const queryClient = useQueryClient();

  // Fetch all available groups
  const { data: groupsResponse, isLoading: groupsLoading } = useQuery({
    queryKey: ["groups"],
    queryFn: () => listGroups(),
    enabled: show,
  });

  const groups: GroupSchemaOut[] = groupsResponse?.data ?? [];

  const { register, handleSubmit, formState, reset, control } = useForm<EditFolderFormData>({
    defaultValues: {
      name: folder.name,
      description: folder.description || "",
      view_group_ids: folder.view_groups?.map((g) => g.id) || [],
      edit_group_ids: folder.edit_groups?.map((g) => g.id) || [],
    },
  });

  // Reset form when modal is opened or folder data changes
  useEffect(() => {
    reset({
      name: folder.name,
      description: folder.description || "",
      view_group_ids: folder.view_groups?.map((g) => g.id) || [],
      edit_group_ids: folder.edit_groups?.map((g) => g.id) || [],
    });
  }, [folder, reset]);

  const updateFolderMutation = useMutation({
    mutationFn: (data: FolderUpdateSchemaIn) =>
      updateFolderInfo({
        path: { folder_id: folder.id },
        body: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folder", folder.id] });
      queryClient.invalidateQueries({ queryKey: ["folderImages"] }); // Invalidate images associated with the folder
      queryClient.invalidateQueries({ queryKey: ["folders"] }); // Invalidate parent folders that might list this folder
      onSaveSuccess();
      handleClose();
    },
    onError: (error) => {
      console.error("Error updating folder:", error);
      // TODO: Display error message to the user
    },
  });

  const onSubmit = async (data: EditFolderFormData) => {
    if (!formState.isDirty) {
      handleClose();
      return;
    }

    const updatedData: FolderUpdateSchemaIn = {};

    if (formState.dirtyFields.description) {
      updatedData.description = data.description === "" ? null : data.description;
    }
    if (formState.dirtyFields.view_group_ids) {
      updatedData.view_group_ids = data.view_group_ids;
    }
    if (formState.dirtyFields.edit_group_ids) {
      updatedData.edit_group_ids = data.edit_group_ids;
    }

    if (Object.keys(updatedData).length === 0) {
      handleClose();
      return;
    }

    updateFolderMutation.mutate(updatedData);
  };

  const groupOptions = groups.map((group) => ({
    value: String(group.id),
    label: group.name,
  }));

  if (groupsLoading) {
    return (
      <Modal show={show} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>Edit Folder</Modal.Title>
        </Modal.Header>
        <Modal.Body className="text-center">
          <Spinner animation="border" />
          <p className="mt-2">Loading groups...</p>
        </Modal.Body>
      </Modal>
    );
  }

  return (
    <Modal show={show} onHide={handleClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Edit Folder</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={handleSubmit(onSubmit)}>
          {updateFolderMutation.isError && (
            <div className="alert alert-danger">Failed to update folder. Please try again.</div>
          )}

          <Form.Group className="mb-3">
            <Form.Label>Name</Form.Label>
            <Form.Control
              type="text"
              value={folder.name}
              readOnly
              className="form-control-plaintext"
              style={{ pointerEvents: "none", userSelect: "none" }}
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              {...register("description")}
              isInvalid={!!formState.errors.description}
            />
            <Form.Control.Feedback type="invalid">
              {formState.errors.description?.message}
            </Form.Control.Feedback>
          </Form.Group>

          {/* View Permissions for Folder */}
          <Form.Group className="mb-4">
            <Form.Label>View Permissions</Form.Label>
            <p className="text-muted small">Select groups that can view this folder.</p>
            <Controller
              name="view_group_ids"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  {...field}
                  isMulti
                  options={groupOptions}
                  getOptionLabel={(option) => option.label}
                  value={groupOptions.filter((option) =>
                    field.value.map(String).includes(option.value),
                  )}
                  onChange={(selectedOptions) =>
                    field.onChange(selectedOptions.map((option) => Number(option.value)))
                  }
                />
              )}
            />
          </Form.Group>

          {/* Edit Permissions for Folder */}
          <Form.Group className="mb-3">
            <Form.Label>Edit Permissions</Form.Label>
            <p className="text-muted small">Select groups that can edit this folder.</p>
            <Controller
              name="edit_group_ids"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  {...field}
                  isMulti
                  options={groupOptions}
                  getOptionLabel={(option) => option.label}
                  value={groupOptions.filter((option) =>
                    field.value.map(String).includes(option.value),
                  )}
                  onChange={(selectedOptions) =>
                    field.onChange(selectedOptions.map((option) => Number(option.value)))
                  }
                />
              )}
            />
          </Form.Group>

          <Modal.Footer>
            <Button variant="secondary" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              type="submit"
              disabled={
                !formState.isDirty || // Disable if no changes
                formState.isSubmitting ||
                updateFolderMutation.isPending
              }
            >
              {formState.isSubmitting || updateFolderMutation.isPending
                ? "Saving..."
                : "Save Changes"}
            </Button>
            {formState.isDirty && <span className="ms-2 text-muted">Unsaved changes</span>}
          </Modal.Footer>
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default EditFolderModal;
