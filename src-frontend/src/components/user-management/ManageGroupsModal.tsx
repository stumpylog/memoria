import type { SubmitHandler } from "react-hook-form";

import React, { useEffect, useMemo } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { GroupOutSchema, UserGroupAssignInSchema, UserOutSchema } from "../../api";

import ThemedSelect from "../common/ThemedSelect";

// Option type for react-select
interface GroupOption {
  value: number;
  label: string;
}

// Define the structure of our form data
interface FormData {
  selectedGroups: GroupOption[];
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
  const { control, handleSubmit, reset } = useForm<FormData>({
    defaultValues: {
      selectedGroups: [],
    },
  });

  // Transform groups into react-select options
  const groupOptions: GroupOption[] = useMemo(
    () =>
      allGroups.map((group) => ({
        value: group.id,
        label: group.name,
      })),
    [allGroups],
  );

  // Get currently selected groups as options
  const selectedGroupOptions: GroupOption[] = useMemo(
    () => groupOptions.filter((option) => userGroupIds.includes(option.value)),
    [groupOptions, userGroupIds],
  );

  // Use effect to reset form values when the user or their group IDs change
  useEffect(() => {
    if (user) {
      reset({
        selectedGroups: selectedGroupOptions,
      });
    } else {
      reset({
        selectedGroups: [],
      });
    }
  }, [user, selectedGroupOptions, reset]);

  // Handle form submission
  const onSubmit: SubmitHandler<FormData> = async (formData) => {
    if (!user) return;

    // Transform the selected groups into the required UserGroupAssignInSchema format
    const groupAssignments: UserGroupAssignInSchema[] = formData.selectedGroups.map((option) => ({
      id: option.value,
    }));

    await handleSave(user.id, groupAssignments);
  };

  return (
    <Modal show={show} onHide={handleClose} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Manage Groups for {user?.username}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3">
            <Form.Label>Select Groups</Form.Label>
            <Controller
              name="selectedGroups"
              control={control}
              render={({ field }) => (
                <ThemedSelect
                  {...field}
                  isMulti
                  options={groupOptions}
                  placeholder="Search and select groups..."
                  isClearable
                  isSearchable
                  closeMenuOnSelect={false}
                  noOptionsMessage={({ inputValue }) =>
                    inputValue ? `No groups found matching "${inputValue}"` : "No groups available"
                  }
                  // Add custom formatting for the placeholder when no groups are available
                  isDisabled={groupOptions.length === 0}
                />
              )}
            />
            {groupOptions.length === 0 && (
              <Form.Text className="text-muted">No groups are available to assign.</Form.Text>
            )}
          </Form.Group>

          <div className="d-flex gap-2">
            <Button variant="primary" type="submit" disabled={loading} className="flex-grow-1">
              {loading ? "Saving..." : "Save Changes"}
            </Button>
            <Button variant="secondary" onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
          </div>
        </Form>
      </Modal.Body>
    </Modal>
  );
};

export default ManageGroupsModal;
