import type { SubmitHandler } from "react-hook-form";

// src/components/UserManagement/ManageGroupsModal.tsx
import React, { useEffect } from "react";
import { Alert, Button, Form, ListGroup, Modal } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { GroupOutSchema, UserGroupAssignInSchema, UserOutSchema } from "../../api";

// Define the structure of our form data
interface FormData {
  // Use a record type to indicate that this object can have string keys
  // and the values associated with those keys are booleans.
  [groupId: string]: boolean;
}

interface ManageGroupsModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userId: number, groupIds: UserGroupAssignInSchema[]) => Promise<void>;
  user: UserOutSchema | null;
  loading: boolean;
  error: string | null;
  allGroups: GroupOutSchema[]; // List of all available groups
  userGroupIds: number[]; // List of IDs of groups the user is currently in
}

const ManageGroupsModal: React.FC<ManageGroupsModalProps> = ({
  show,
  handleClose,
  handleSave,
  user,
  loading,
  error,
  allGroups,
  userGroupIds,
}) => {
  // Initialize react-hook-form
  const { register, handleSubmit, reset } = useForm<FormData>({
    defaultValues: {}, // Default values will be set dynamically in the effect
  });

  // Use effect to reset form values when the user or their group IDs change
  useEffect(() => {
    if (user) {
      // Map the userGroupIds into the FormData structure for default values
      // Explicitly type the accumulator as FormData to resolve the type error
      const defaultValues: FormData = allGroups.reduce((acc: FormData, group) => {
        acc[group.id.toString()] = userGroupIds.includes(group.id);
        return acc;
      }, {} as FormData); // Also cast the initial value for clarity

      reset(defaultValues); // Reset the form with the correct default values
    } else {
      // If no user, reset to empty
      reset({});
    }
    // Added allGroups to dependencies as it's used in the effect to build defaultValues
  }, [userGroupIds, user, reset, allGroups]);

  // Handle form submission
  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    if (!user) return;

    // Transform the form data back into the required UserGroupAssignInSchema format
    const groupAssignments: UserGroupAssignInSchema[] = Object.entries(formData)
      // Use '_' to indicate intentional unused variables in destructuring
      .filter(([_, isSelected]) => isSelected) // Keep only selected groups
      .map(([groupId, _]) => ({ id: parseInt(groupId, 10) })); // Map to the required object structure

    await handleSave(user.id, groupAssignments);
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Manage Groups for {user?.username}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {/* Use the form's handleSubmit */}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Label>Select Groups</Form.Label>
          <ListGroup style={{ maxHeight: "300px", overflowY: "auto" }}>
            {allGroups.map((group) => (
              <ListGroup.Item key={group.id}>
                <Form.Check
                  type="checkbox"
                  label={group.name}
                  // Use the register function to connect the input to react-hook-form
                  // The name should match the key in the FormData interface (group ID as string)
                  {...register(group.id.toString())}
                  // react-hook-form handles 'checked' state internally when registered
                />
              </ListGroup.Item>
            ))}
            {allGroups.length === 0 && <ListGroup.Item>No groups available.</ListGroup.Item>}
          </ListGroup>
          {/* The submit button should be inside the form */}
          <Button
            variant="primary"
            type="submit" // Set type to submit
            disabled={loading}
            className="mt-3 w-100" // Added some spacing and full width
          >
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        {/* Close button remains outside the form */}
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default ManageGroupsModal;
