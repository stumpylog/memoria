// src/components/EditPersonModal.tsx

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { GroupSchemaOut, PersonDetailOutSchema, PersonUpdateInSchema } from "../../api";

import {
  listGroupsOptions,
  updatePersonDetailMutation,
} from "../../api/@tanstack/react-query.gen";
import ThemedSelect from "../common/ThemedSelect";

interface EditPersonModalProps {
  show: boolean;
  handleClose: () => void;
  person: PersonDetailOutSchema;
  onSaveSuccess: (updatedPerson: PersonDetailOutSchema) => void;
}

// Define form data type, adding group IDs
interface EditPersonFormData {
  name: string;
  description: string | null;
  view_group_ids: number[]; // Add view_group_ids
  edit_group_ids: number[]; // Add edit_group_ids
}

const EditPersonModal: React.FC<EditPersonModalProps> = ({
  show,
  handleClose,
  person,
  onSaveSuccess,
}) => {
  const queryClient = useQueryClient(); // Initialize query client

  // Fetch all available groups
  const { data: groupsResponse, isLoading: groupsLoading } = useQuery({
    ...listGroupsOptions(),
    enabled: show, // Only fetch when modal is open
  });

  const groups: GroupSchemaOut[] = groupsResponse ?? [];

  const { register, handleSubmit, formState, reset, control } = useForm<EditPersonFormData>({
    defaultValues: {
      name: person.name,
      description: person.description || "",
      view_group_ids: person.view_groups?.map((g) => g.id) || [], // Initialize
      edit_group_ids: person.edit_groups?.map((g) => g.id) || [], // Initialize
    },
  });

  // Reset form when modal is opened or person data changes
  useEffect(() => {
    reset({
      name: person.name,
      description: person.description || "",
      view_group_ids: person.view_groups?.map((g) => g.id) || [],
      edit_group_ids: person.edit_groups?.map((g) => g.id) || [],
    });
  }, [person, reset]);

  const updatePersonMutation = useMutation({
    ...updatePersonDetailMutation(),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["person", person.id] }); // Invalidate person details
      // Invalidate images that might be affected by permission changes
      queryClient.invalidateQueries({ queryKey: ["person-image-ids"] });
      queryClient.invalidateQueries({ queryKey: ["person-images-thumbnails"] });

      if (response) {
        onSaveSuccess(response);
      } else {
        onSaveSuccess(person);
      }
      handleClose();
    },
    onError: (error) => {
      console.error("Error updating person:", error);
      // TODO: Display error message to the user
    },
  });

  const onSubmit = async (data: EditPersonFormData) => {
    if (!formState.isDirty) {
      handleClose();
      return;
    }

    const updatedData: PersonUpdateInSchema = {};

    if (formState.dirtyFields.name) {
      updatedData.name = data.name;
    }
    if (formState.dirtyFields.description) {
      updatedData.description = data.description === "" ? null : data.description;
    }
    // Add group IDs to updatedData if they are dirty
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

    updatePersonMutation.mutate({
      path: { person_id: person.id },
      body: updatedData,
    }); // Use the mutation
  };

  // Prepare options for react-select - Convert value to string
  const groupOptions = groups.map((group) => ({
    value: String(group.id), // Convert number to string here
    label: group.name,
  }));

  if (groupsLoading) {
    return (
      <Modal show={show} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>Edit Person</Modal.Title>
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
        <Modal.Title>Edit Person</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={handleSubmit(onSubmit)}>
          {updatePersonMutation.isError && (
            <div className="alert alert-danger">Failed to update person. Please try again.</div>
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

          {/* View Permissions for Person */}
          <Form.Group className="mb-4">
            <Form.Label>View Permissions</Form.Label>
            <p className="text-muted small">Select groups that can view this person.</p>
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

          {/* Edit Permissions for Person */}
          <Form.Group className="mb-3">
            <Form.Label>Edit Permissions</Form.Label>
            <p className="text-muted small">Select groups that can edit this person.</p>
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
              disabled={formState.isSubmitting || updatePersonMutation.isPending}
            >
              {formState.isSubmitting || updatePersonMutation.isPending
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

export default EditPersonModal;
