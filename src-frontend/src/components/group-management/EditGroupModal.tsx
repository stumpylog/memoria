import type { SubmitHandler } from "react-hook-form";

// src/components/group-management/EditGroupModal.tsx
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { GroupOutSchema, GroupUpdateInSchema } from "../../api";

interface EditGroupModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (groupId: number, groupData: GroupUpdateInSchema) => Promise<void>;
  group: GroupOutSchema | null; // The group being edited
  loading: boolean;
  error: string | null; // API error from the parent
}

// Define the type for our form data
interface FormValues {
  name: string;
}

const EditGroupModal: React.FC<EditGroupModalProps> = ({
  show,
  handleClose,
  handleSave,
  group,
  loading,
  error,
}) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<FormValues>({
    // Use defaultValues to initialize the form. This will be updated by the effect below.
    defaultValues: {
      name: "",
    },
    mode: "onChange", // Optional: Validate on change
  });

  // Effect to populate form when modal is shown or selected group changes, and reset on close
  useEffect(() => {
    if (show && group) {
      // Use reset to set the form values and also reset the dirty state
      reset({ name: group.name });
    } else if (!show) {
      // Optionally reset form to default empty state when closed
      reset({ name: "" });
    }
    // Note: We don't need to manage localError state anymore as react-hook-form handles input errors
  }, [show, group, reset]); // Include reset in the dependency array

  // Handle form submission
  const onSubmit: SubmitHandler<FormValues> = async (data) => {
    if (!group) return; // Should not happen if modal is shown with a group

    const groupData: GroupUpdateInSchema = { name: data.name };

    try {
      await handleSave(group.id, groupData);
      // handleSave's onSuccess should close the modal and invalidate queries
      // The parent component will handle closing the modal on successful save.
    } catch (err: any) {
      // Error is handled by the parent component's mutation onError
      // The parent 'error' prop will show the actual API error.
      console.error("Failed to update group:", err);
    }
  };

  // Don't render if no group is selected and the modal is trying to show
  if (!group && show) {
    return null;
  }

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Group: {group?.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {/* Display combined errors: react-hook-form input errors or external API errors */}
        {(errors.name || error) && <Alert variant="danger">{errors.name?.message || error}</Alert>}
        {/* Use react-hook-form's handleSubmit to wrap the onSubmit logic */}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="formGroupName">
            <Form.Label>Group Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter new group name"
              // Register the input with react-hook-form
              {...register("name", { required: "Group name cannot be empty." })}
              isInvalid={!!errors.name} // Use react-hook-form errors to determine invalid state
              disabled={loading} // Disable input while saving
            />
            {/* Display validation feedback from react-hook-form */}
            <Form.Control.Feedback type="invalid">{errors.name?.message}</Form.Control.Feedback>
          </Form.Group>
          {/* You can add other form fields here and register them similarly */}
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        {/* The Save button now uses type="submit" and is part of the form.
             Disabled based on loading state AND if the form is not dirty or has errors. */}
        <Button
          variant="primary"
          type="submit" // This button will trigger form submission
          onClick={handleSubmit(onSubmit)} // Use handleSubmit here as well for robustness
          disabled={loading || !isDirty || !!errors.name} // Disable if loading, not dirty, or has validation errors
          form="formGroupName" // Associate button with the form using its id
        >
          {loading ? (
            <>
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              {" Saving..."}
            </>
          ) : (
            "Save Changes"
          )}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default EditGroupModal;
