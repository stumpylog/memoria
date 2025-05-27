// src/components/EditFolderModal.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";
import Select from "react-select";

import type { FolderDetailSchemaOut, FolderUpdateSchemaIn, GroupSchemaOut } from "../../api";

import { groupGetAll, updateFolderInfo } from "../../api";
import { useTheme } from "../../hooks/useTheme";

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
  const { effectiveTheme } = useTheme();
  const isDarkTheme = effectiveTheme === "dark";

  // Fetch all available groups
  const { data: groupsResponse, isLoading: groupsLoading } = useQuery({
    queryKey: ["groups"],
    queryFn: () => groupGetAll(),
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

    if (formState.dirtyFields.name) {
      updatedData.name = data.name;
    }
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

  const customStyles = {
    control: (provided: any, state: any) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff",
      borderColor: isDarkTheme ? "#495057" : "#ced4da",
      color: isDarkTheme ? "#f8f9fa" : "#212529",
      "&:hover": {
        borderColor: isDarkTheme ? "#6c757d" : "#adb5bd",
      },
      boxShadow: state.isFocused
        ? isDarkTheme
          ? "0 0 0 0.2rem rgba(108,117,125,.25)"
          : "0 0 0 0.2rem rgba(0,123,255,.25)"
        : null,
    }),
    singleValue: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    input: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    placeholder: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#adb5bd" : "#6c757d",
    }),
    menu: (provided: any) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff",
      borderColor: isDarkTheme ? "#495057" : "#ced4da",
    }),
    option: (provided: any, state: any) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? isDarkTheme
          ? "#007bff"
          : "#007bff"
        : state.isFocused
          ? isDarkTheme
            ? "#495057"
            : "#e9ecef"
          : isDarkTheme
            ? "#343a40"
            : "#fff",
      color: state.isSelected ? "#fff" : isDarkTheme ? "#f8f9fa" : "#212529",
      "&:active": {
        backgroundColor: isDarkTheme ? "#0056b3" : "#0056b3",
      },
    }),
    multiValue: (provided: any) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#007bff" : "#e0f7fa",
      color: isDarkTheme ? "#fff" : "#000",
    }),
    multiValueLabel: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#fff" : "#000",
    }),
    multiValueRemove: (provided: any) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#6c757d",
      "&:hover": {
        backgroundColor: isDarkTheme ? "#dc3545" : "#dc3545",
        color: "white",
      },
    }),
  };

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
              {...register("name", { required: "Name is required" })}
              isInvalid={!!formState.errors.name}
            />
            <Form.Control.Feedback type="invalid">
              {formState.errors.name?.message}
            </Form.Control.Feedback>
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
                <Select
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
                  styles={customStyles}
                  theme={(currentTheme) => ({
                    ...currentTheme,
                    colors: {
                      ...currentTheme.colors,
                      primary: isDarkTheme ? "#007bff" : "#007bff",
                      primary25: isDarkTheme ? "#495057" : "#e9ecef",
                      neutral0: isDarkTheme ? "#343a40" : "#fff",
                      neutral80: isDarkTheme ? "#f8f9fa" : "#212529",
                      neutral20: isDarkTheme ? "#495057" : "#ced4da",
                    },
                  })}
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
                <Select
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
                  styles={customStyles}
                  theme={(currentTheme) => ({
                    ...currentTheme,
                    colors: {
                      ...currentTheme.colors,
                      primary: isDarkTheme ? "#007bff" : "#007bff",
                      primary25: isDarkTheme ? "#495057" : "#e9ecef",
                      neutral0: isDarkTheme ? "#343a40" : "#fff",
                      neutral80: isDarkTheme ? "#f8f9fa" : "#212529",
                      neutral20: isDarkTheme ? "#495057" : "#ced4da",
                    },
                  })}
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
              disabled={formState.isSubmitting || updateFolderMutation.isPending}
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
