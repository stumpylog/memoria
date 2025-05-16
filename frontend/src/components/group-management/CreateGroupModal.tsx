// src/components/group-management/CreateGroupModal.tsx
import type { SubmitHandler } from "react-hook-form";

import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { GroupCreateInSchema } from "../../api";

// Define the structure of our form data
interface FormData {
  name: string;
}

interface CreateGroupModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (groupData: GroupCreateInSchema) => Promise<void>;
  loading: boolean;
  error: string | null; // This prop is for API errors from the parent
}

const CreateGroupModal: React.FC<CreateGroupModalProps> = ({
  show,
  handleClose,
  handleSave,
  loading,
  error, // API error prop
}) => {
  // Initialize react-hook-form
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isValid }, // Destructure errors, isDirty, and isValid
  } = useForm<FormData>({
    defaultValues: {
      name: "", // Set the default value for the form field
    },
    mode: "onChange", // Validate on change to update isValid and errors status
  });

  // Effect to reset the form when the modal is shown
  useEffect(() => {
    if (show) {
      reset({ name: "" }); // Reset form values and states (dirty, errors)
    }
  }, [show, reset]);

  // Handle form submission
  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    // handleSubmit will only call this function if the form is valid
    // based on the 'required' rule provided in register.

    // The formData already matches GroupCreateInSchema structure
    await handleSave(formData);
    // Assuming handleSave's success/error handling (like closing modal,
    // query invalidation, or showing the 'error' prop) is done by the parent.
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Create New Group</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {/* Display parent-provided API error */}
        {error && <Alert variant="danger">{error}</Alert>}
        {/* Use the form's handleSubmit */}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter group name"
              // Use register to connect the input to react-hook-form
              // Provide built-in validation rules here
              {...register("name", { required: "Group name cannot be empty" })}
              isInvalid={!!errors.name} // Use errors object for validation feedback
              disabled={loading}
            />
            {/* Display validation error message */}
            <Form.Control.Feedback type="invalid">{errors.name?.message}</Form.Control.Feedback>
          </Form.Group>
          {/* The submit button */}
          <Button
            variant="primary"
            type="submit" // Set type to submit
            disabled={loading || !isDirty || !isValid} // Disable if loading, not dirty, or not valid
            className="mt-3 w-100" // Added some spacing and full width
          >
            {loading ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                {" Saving..."}
              </>
            ) : (
              "Save Group"
            )}
          </Button>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        {/* Cancel button remains outside the form */}
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateGroupModal;
