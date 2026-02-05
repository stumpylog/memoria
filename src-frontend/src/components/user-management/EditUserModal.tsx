// src/components/UserManagement/EditUserModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { UserOutSchema, UserUpdateInSchemeWritable } from "../../api";

import { usersListQueryKey, usersUpdateMutation } from "../../api/@tanstack/react-query.gen";
import { getErrorMessage } from "../../utils/getErrorMessage";

interface EditUserFormData {
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  password?: string;
}

interface EditUserModalProps {
  show: boolean;
  handleClose: () => void;
  user: UserOutSchema;
  onSuccess?: () => void;
}

const EditUserModal: React.FC<EditUserModalProps> = ({ show, handleClose, user, onSuccess }) => {
  const queryClient = useQueryClient();

  const {
    mutateAsync,
    isPending,
    error,
    reset: resetMutation,
  } = useMutation({
    ...usersUpdateMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: usersListQueryKey() });
      onSuccess?.();
      handleClose();
    },
  });

  const {
    control,
    register,
    handleSubmit,
    reset: resetForm,
    formState: { errors, isDirty, dirtyFields },
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

  useEffect(() => {
    if (show && user) {
      resetForm({
        email: user.email ?? null,
        first_name: user.first_name ?? null,
        last_name: user.last_name ?? null,
        is_active: user.is_active ?? true,
        is_staff: user.is_staff ?? false,
        is_superuser: user.is_superuser ?? false,
        password: "",
      });
      resetMutation();
    }
  }, [show, user, resetForm, resetMutation]);

  const onSubmit: SubmitHandler<EditUserFormData> = async (formData) => {
    const passwordChanged = !!formData.password;

    if (!isDirty && !passwordChanged) {
      handleClose();
      return;
    }

    const dataToSave: UserUpdateInSchemeWritable = {};

    (Object.keys(formData) as Array<keyof EditUserFormData>).forEach((key) => {
      if (key === "password") return;

      if (dirtyFields[key]) {
        const value = formData[key];

        if (key === "email" || key === "first_name" || key === "last_name") {
          (dataToSave[key] as string | null) = value === "" ? null : (value as string | null);
        } else if (typeof value === "boolean") {
          (dataToSave[key] as boolean) = value;
        }
      }
    });

    if (passwordChanged) {
      dataToSave.password = formData.password;
    }

    if (Object.keys(dataToSave).length === 0) {
      handleClose();
      return;
    }

    await mutateAsync({
      path: { user_id: user.id },
      body: dataToSave,
    });
  };

  const errorMessage = getErrorMessage(error);

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Edit User: {user.username}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}

          <Form.Group className="mb-3" controlId="formUsernameReadonly">
            <Form.Label>Username</Form.Label>
            <Form.Control type="text" value={user.username} readOnly disabled />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formPassword">
            <Form.Label>Password (Leave blank to keep current)</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter new password"
              {...register("password")}
              disabled={isPending}
            />
            {errors.password && <p className="text-danger">{errors.password.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formEmail">
            <Form.Label>Email address</Form.Label>
            <Form.Control
              type="email"
              placeholder="Enter email"
              {...register("email")}
              disabled={isPending}
            />
            {errors.email && <p className="text-danger">{errors.email.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formFirstName">
            <Form.Label>First Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter first name"
              {...register("first_name")}
              disabled={isPending}
            />
            {errors.first_name && <p className="text-danger">{errors.first_name.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formLastName">
            <Form.Label>Last Name</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter last name"
              {...register("last_name")}
              disabled={isPending}
            />
            {errors.last_name && <p className="text-danger">{errors.last_name.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsActive">
            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Active"
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isPending}
                />
              )}
            />
            {errors.is_active && <p className="text-danger">{errors.is_active.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsStaff">
            <Controller
              name="is_staff"
              control={control}
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Staff"
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isPending}
                />
              )}
            />
            {errors.is_staff && <p className="text-danger">{errors.is_staff.message}</p>}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsSuperuser">
            <Controller
              name="is_superuser"
              control={control}
              render={({ field }) => (
                <Form.Check
                  type="checkbox"
                  label="Is Superuser"
                  name={field.name}
                  onChange={field.onChange}
                  onBlur={field.onBlur}
                  ref={field.ref}
                  checked={field.value}
                  disabled={isPending}
                />
              )}
            />
            {errors.is_superuser && <p className="text-danger">{errors.is_superuser.message}</p>}
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose} disabled={isPending}>
            Close
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isPending || (!isDirty && !getValues("password"))}
          >
            {isPending ? "Saving..." : "Save Changes"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default EditUserModal;
