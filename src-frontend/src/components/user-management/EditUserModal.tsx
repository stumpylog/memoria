// src/components/UserManagement/EditUserModal.tsx
import type { SubmitHandler } from "react-hook-form";

import React, { useEffect, useState } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { UserOutSchema, UserUpdateInSchemeWritable } from "../../api";

interface EditUserFormData {
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  password?: string; // Password is optional for submission
}

interface EditUserModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userId: number, userData: UserUpdateInSchemeWritable) => Promise<void>;
  user: UserOutSchema | null;
  loading: boolean;
  error: string | null;
}

const EditUserModal: React.FC<EditUserModalProps> = ({
  show,
  handleClose,
  handleSave,
  user,
  loading,
  error,
}) => {
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty, dirtyFields },
    getValues,
  } = useForm<EditUserFormData>({
    defaultValues: {
      email: null,
      first_name: null,
      last_name: null,
      is_active: true,
      is_staff: false,
      is_superuser: false,
      password: "",
    },
  });

  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      const initialData: EditUserFormData = {
        email: user.email ?? null,
        first_name: user.first_name ?? null,
        last_name: user.last_name ?? null,
        is_active: user.is_active ?? true,
        is_staff: user.is_staff ?? false,
        is_superuser: user.is_superuser ?? false,
        password: "",
      };
      reset(initialData);
      setLocalError(null);
    } else {
      reset({
        email: null,
        first_name: null,
        last_name: null,
        is_active: true,
        is_staff: false,
        is_superuser: false,
        password: "",
      });
      setLocalError(null);
    }
  }, [user, reset]);

  const onSubmit: SubmitHandler<EditUserFormData> = async (formData) => {
    if (!user) {
      setLocalError("No user selected for editing.");
      return;
    }

    setLocalError(null);

    // Check if any fields managed by react-hook-form are dirty OR if the password field is filled
    // We check the password separately because its initial value is always "", so isDirty wouldn't
    // detect a change from "" to a value unless the initial default was something else.
    const passwordChanged = !!formData.password; // Check if password has a non-empty value

    // Use isDirty from formState to check for changes in tracked fields
    if (!isDirty && !passwordChanged) {
      console.log("No changes detected.");
      handleClose(); // Close modal as nothing needs saving
      return;
    }

    const dataToSave: UserUpdateInSchemeWritable = {};

    // Iterate over form data and add fields to dataToSave if they are dirty
    // dirtyFields tells us which fields were modified. We get the current value from formData.
    (Object.keys(formData) as Array<keyof EditUserFormData>).forEach((key) => {
      // Exclude password from this general dirty check unless it's the password field itself
      if (key === "password") {
        // Password handled separately below
        return;
      }

      // Check if the field is marked as dirty by react-hook-form
      if (dirtyFields && dirtyFields[key]) {
        const value = formData[key];

        // Handle specific type conversions if necessary (e.g., "" to null for strings)
        if (key === "email" || key === "first_name" || key === "last_name") {
          // For optional string fields, convert empty string to null if that's the API expectation
          (dataToSave[key] as string | null) = value === "" ? null : (value as string | null);
        } else {
          // For other fields (like booleans), add the value directly
          // Use type assertion to match UserUpdateInScheme field type
          if (typeof value === "boolean") {
            (dataToSave[key] as boolean) = value;
          } else if (value === null) {
            // If the form value is null and the original wasn't, we should send null
            (dataToSave[key] as any) = value; // Using 'any' as a fallback if complex union types
          }
        }
      }
    });

    // Include password only if it was entered (the field is not empty)
    if (passwordChanged) {
      dataToSave.password = formData.password;
    }

    // This check should technically be redundant due to the !isDirty && !passwordChanged check above,
    // but leaving it for safety.
    if (Object.keys(dataToSave).length === 0) {
      console.log("No changes detected (post-processing check).");
      handleClose();
      return;
    }

    console.log("Saving changes:", dataToSave);

    try {
      // Pass the partial dataToSave object to the handleSave function
      await handleSave(user.id, dataToSave);
      // handleSave in parent should close the modal on success
    } catch (err: any) {
      console.error(`Failed to update user ${user.id}:`, err);
      // Use parent error state or local error state
      // setLocalError(err.message || `Failed to update user ${user.id}.`); // If using local error
    } finally {
      // The parent component should handle loading state based on the handleSave promise
    }
  };

  // Determine if we should show a loading spinner/disable inputs
  // Use parent loading state OR react-hook-form's isSubmitting state
  const isLoading = loading || isSubmitting;

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Edit User: {user?.username}</Modal.Title>
      </Modal.Header>
      {/* Wrap the form content in react-bootstrap Form and attach handleSubmit */}
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {/* Display either parent error or local error */}
          {(error || localError) && <Alert variant="danger">{error || localError}</Alert>}
          {/* Display react-hook-form validation errors if any */}
          {/* {Object.keys(errors).length > 0 && (
              <Alert variant="warning">Please fix the errors in the form.</Alert>
          )} */}

          {/* Username is typically not editable via this form */}
          <Form.Group className="mb-3" controlId="formUsernameReadonly">
            <Form.Label>Username</Form.Label>
            <Form.Control type="text" value={user?.username || ""} readOnly disabled />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formPassword">
            <Form.Label>Password (Leave blank to keep current)</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter new password"
              // Use register to connect the input to react-hook-form state
              {...register("password")}
              disabled={isLoading}
            />
            {/* Display react-hook-form password errors if any */}
            {errors.password && <p className="text-danger">{errors.password.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formEmail">
            <Form.Label>Email address</Form.Label>
            <Form.Control
              type="email"
              placeholder="Enter email"
              // Use register to connect the input to react-hook-form state
              {...register("email")}
              disabled={isLoading}
            />
            {/* Display react-hook-form email errors if any */}
            {errors.email && <p className="text-danger">{errors.email.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formFirstName">
            <Form.Label>First Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter first name"
              // Use register to connect the input to react-hook-form state
              {...register("first_name")}
              disabled={isLoading}
            />
            {/* Display react-hook-form first_name errors if any */}
            {errors.first_name && <p className="text-danger">{errors.first_name.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formLastName">
            <Form.Label>Last Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter last name"
              // Use register to connect the input to react-hook-form state
              {...register("last_name")}
              disabled={isLoading}
            />
            {/* Display react-hook-form last_name errors if any */}
            {errors.last_name && <p className="text-danger">{errors.last_name.message}</p>}
          </Form.Group>

          {/* Use Controller for checkboxes - Corrected prop mapping */}
          <Form.Group className="mb-3" controlId="formIsActive">
            <Controller
              name="is_active"
              control={control}
              // defaultValue={true} // Can set default here or in useForm
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Active"
                  // Manually wire up field props to Form.Check props
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isLoading}
                />
              )}
            />
            {/* Display react-hook-form is_active errors if any */}
            {errors.is_active && <p className="text-danger">{errors.is_active.message}</p>}
          </Form.Group>

          {/* Use Controller for checkboxes - Corrected prop mapping */}
          <Form.Group className="mb-3" controlId="formIsStaff">
            <Controller
              name="is_staff"
              control={control}
              // defaultValue={false} // Can set default here or in useForm
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Staff"
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isLoading}
                />
              )}
            />
            {/* Display react-hook-form is_staff errors if any */}
            {errors.is_staff && <p className="text-danger">{errors.is_staff.message}</p>}
          </Form.Group>

          {/* Use Controller for checkboxes - Corrected prop mapping */}
          <Form.Group className="mb-3" controlId="formIsSuperuser">
            <Controller
              name="is_superuser"
              control={control}
              // defaultValue={false} // Can set default here or in useForm
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Superuser"
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isLoading}
                />
              )}
            />
            {/* Display react-hook-form is_superuser errors if any */}
            {errors.is_superuser && <p className="text-danger">{errors.is_superuser.message}</p>}
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose} disabled={isLoading}>
            Close
          </Button>
          {/* The submit button triggers react-hook-form's handleSubmit */}
          {/* Disable save button if no changes have been made and password is empty */}
          <Button
            variant="primary"
            type="submit"
            disabled={isLoading || (!isDirty && !getValues("password"))}
          >
            {isLoading ? "Saving..." : "Save Changes"}
          </Button>
        </Modal.Footer>
      </Form>{" "}
      {/* Close the Form tag */}
    </Modal>
  );
};

export default EditUserModal;
