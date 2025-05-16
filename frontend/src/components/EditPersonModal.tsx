import React, { useEffect } from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { PersonDetailOutSchema, PersonUpdateInSchema } from "../api";

import { updatePersonDetail } from "../api";

interface EditPersonModalProps {
  show: boolean;
  handleClose: () => void;
  person: PersonDetailOutSchema;
  onSaveSuccess: () => void; // Callback to refetch data
}

// Define form data type
interface EditPersonFormData {
  name: string;
  description: string | null;
}

const EditPersonModal: React.FC<EditPersonModalProps> = ({
  show,
  handleClose,
  person,
  onSaveSuccess,
}) => {
  const { register, handleSubmit, formState, reset } = useForm<EditPersonFormData>({
    defaultValues: {
      name: person.name,
      description: person.description || "", // Initialize with empty string if null for form
    },
  });

  // Reset form when modal is opened or person data changes
  useEffect(() => {
    reset({
      name: person.name,
      description: person.description || "",
    });
  }, [person, reset]);

  const onSubmit = async (data: EditPersonFormData) => {
    if (!formState.isDirty) {
      handleClose(); // Close if no changes
      return;
    }

    const updatedData: PersonUpdateInSchema = {};

    // Only add fields that have been changed to the update payload
    if (formState.dirtyFields.name) {
      updatedData.name = data.name;
    }
    if (formState.dirtyFields.description) {
      // Send null if the field is empty in the form
      updatedData.description = data.description === "" ? null : data.description;
    }

    if (Object.keys(updatedData).length === 0) {
      handleClose(); // Close if no dirty fields resulted in update data
      return;
    }

    try {
      // Assuming person.id is the person_id
      await updatePersonDetail({ path: { person_id: person.id }, body: updatedData });
      onSaveSuccess(); // Call the refetch callback
      handleClose();
    } catch (error) {
      console.error("Error updating person:", error);
      // TODO: Display error message to the user
    }
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Edit Person</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3">
            <Form.Label>Name</Form.Label>
            <Form.Control
              type="text"
              {...register("name", { required: "Name is required" })} // Add validation
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
          <Button variant="primary" type="submit" disabled={formState.isSubmitting}>
            Save Changes
          </Button>
          {formState.isDirty && <span className="ms-2 text-muted">Unsaved changes</span>}
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default EditPersonModal;
