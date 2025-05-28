// src/components/EditPetModal.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";
import Select from "react-select";

import type { PetReadDetailSchemaOut, PetTypeChoices, PetUpdateInSchema } from "../../api";

import { updatePet } from "../../api";
import { useTheme } from "../../hooks/useTheme";

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
  const { effectiveTheme } = useTheme();
  const isDarkTheme = effectiveTheme === "dark";

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

  const updatePetMutation = useMutation({
    mutationFn: (data: PetUpdateInSchema) => updatePet({ path: { pet_id: pet.id }, body: data }),
    onSuccess: (data) => {
      onSaveSuccess(data.data); // Pass the updated pet data
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
      updatePetMutation.mutate(updatedFields);
    } else {
      handleClose(); // Close if no changes
    }
  };

  // Custom styles for react-select to match theme
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
                <Select
                  inputId="editPetTypeSelect"
                  options={petTypeSelectOptions}
                  isClearable
                  placeholder="Select a pet type..."
                  styles={customStyles}
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
              disabled={formState.isSubmitting || updatePetMutation.isPending}
            >
              {formState.isSubmitting || updatePetMutation.isPending
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
