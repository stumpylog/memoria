// src/components/EditPetModal.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { PetReadDetailSchemaOut, PetTypeChoices, PetUpdateInSchema } from "../../api";

import { updatePetMutation } from "../../api/@tanstack/react-query.gen";
import ThemedSelect from "../common/ThemedSelect";

// Define a runtime constant for pet types here, outside the API generated file
// In a larger application, consider moving this to a shared utils/constants.ts
const PET_TYPE_OPTIONS = ["cat", "dog", "horse"] as const;

interface EditPetModalProps {
  show: boolean;
  handleClose: () => void;
  pet: PetReadDetailSchemaOut;
  onSaveSuccess: (updatedPet: PetReadDetailSchemaOut) => void;
}

// Define form data type
interface EditPetFormData {
  name: string;
  description: string | null;
  pet_type: PetTypeChoices | null; // Allow null for pet_type
}

const EditPetModal: React.FC<EditPetModalProps> = ({ show, handleClose, pet, onSaveSuccess }) => {
  const queryClient = useQueryClient();

  const { control, handleSubmit, reset, formState } = useForm<EditPetFormData>({
    defaultValues: {
      name: pet.name,
      description: pet.description,
      pet_type: pet.pet_type, // Set default from existing pet data
    },
  });

  // Reset form when modal opens or pet data changes
  useEffect(() => {
    if (show) {
      reset({
        name: pet.name,
        description: pet.description,
        pet_type: pet.pet_type,
      });
    }
  }, [show, pet, reset]);

  const updatePetMutationResult = useMutation({
    ...updatePetMutation(),
    onSuccess: (data) => {
      if (data === undefined) {
        throw new Error();
      }
      onSaveSuccess(data); // Pass the updated pet data
      queryClient.invalidateQueries({ queryKey: ["pet", pet.id] }); // Invalidate specific pet query
      queryClient.invalidateQueries({ queryKey: ["pets"] }); // Invalidate pet list query
    },
    onError: (error) => {
      console.error("Error updating pet:", error);
      // Optionally, display an error message to the user
    },
  });

  const onSubmit = (data: EditPetFormData) => {
    // Only send changed fields
    const updatedFields: PetUpdateInSchema = {};
    if (data.name !== pet.name) updatedFields.name = data.name;
    if (data.description !== pet.description) updatedFields.description = data.description;
    if (data.pet_type !== pet.pet_type) updatedFields.pet_type = data.pet_type;

    if (Object.keys(updatedFields).length > 0) {
      updatePetMutationResult.mutate({ path: { pet_id: pet.id }, body: updatedFields });
    } else {
      handleClose(); // Close if no changes
    }
  };

  // Options for react-select Pet Type filter using the local constant
  const petTypeSelectOptions = PET_TYPE_OPTIONS.map((type) => ({
    value: type,
    label: type.charAt(0).toUpperCase() + type.slice(1),
  }));

  return (
    <Modal show={show} onHide={handleClose} centered size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Edit Pet: {pet.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="editPetName">
            <Form.Label>Name</Form.Label>
            <Controller
              name="name"
              control={control}
              rules={{ required: "Pet name is required" }}
              render={({ field, fieldState }) => (
                <>
                  <Form.Control type="text" {...field} isInvalid={!!fieldState.error} />
                  <Form.Control.Feedback type="invalid">
                    {fieldState.error?.message}
                  </Form.Control.Feedback>
                </>
              )}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="editPetDescription">
            <Form.Label>Description</Form.Label>
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <Form.Control
                  as="textarea"
                  rows={3}
                  {...field}
                  value={field.value || ""} // Ensure controlled component
                />
              )}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="editPetType">
            <Form.Label>Pet Type</Form.Label>
            <Controller
              name="pet_type"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  inputId="editPetTypeSelect"
                  options={petTypeSelectOptions}
                  isClearable
                  placeholder="Select a pet type..."
                  value={petTypeSelectOptions.find((opt) => opt.value === field.value) || null}
                  onChange={(selectedOption) => {
                    field.onChange(selectedOption?.value ?? null);
                  }}
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
              disabled={formState.isSubmitting || updatePetMutationResult.isPending}
            >
              {formState.isSubmitting || updatePetMutationResult.isPending
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

export default EditPetModal;
