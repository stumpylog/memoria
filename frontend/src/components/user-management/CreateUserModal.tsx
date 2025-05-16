// src/components/UserManagement/CreateUserModal.tsx
import type { SubmitHandler } from "react-hook-form";

import React, { useEffect, useMemo } from "react"; // Import useMemo
import { Alert, Button, Form, Modal } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { UserInCreateSchemaWritable } from "../../api";

interface CreateUserModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userData: UserInCreateSchemaWritable) => Promise<void>;
  loading: boolean;
  error: string | null;
}

type CreateUserFormData = UserInCreateSchemaWritable & {
  email: string;
  first_name: string;
  last_name: string;
};

const CreateUserModal: React.FC<CreateUserModalProps> = ({
  show,
  handleClose,
  handleSave,
  loading,
  error,
}) => {
  // Use useMemo to memoize the defaultValues object
  const defaultValues: CreateUserFormData = useMemo(
    () => ({
      username: "",
      password: "",
      email: "",
      first_name: "",
      last_name: "",
      is_active: true,
      is_staff: false,
      is_superuser: false,
    }),
    [],
  ); // Empty dependency array means this object is created once

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateUserFormData>({
    defaultValues: defaultValues,
  });

  // Reset the form when the modal is opened using the memoized defaultValues
  useEffect(() => {
    if (show) {
      reset(defaultValues);
    }
  }, [show, reset, defaultValues]); // defaultValues is now a stable reference

  const onSubmit: SubmitHandler<CreateUserFormData> = async (data) => {
    const userDataToSave: UserInCreateSchemaWritable = {
      ...data,
      email: data.email === "" ? null : data.email,
      first_name: data.first_name === "" ? null : data.first_name,
      last_name: data.last_name === "" ? null : data.last_name,
    };
    await handleSave(userDataToSave);
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Create New User</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="formUsername">
            <Form.Label>Username</Form.Label>
            <Form.Control
              type="text"
              {...register("username", { required: "Username is required" })}
              isInvalid={!!errors.username}
            />
            {errors.username && (
              <Form.Control.Feedback type="invalid">
                {errors.username.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formPassword">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              {...register("password", { required: "Password is required" })}
              isInvalid={!!errors.password}
            />
            {errors.password && (
              <Form.Control.Feedback type="invalid">
                {errors.password.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formEmail">
            <Form.Label>Email address</Form.Label>
            <Form.Control type="email" {...register("email")} isInvalid={!!errors.email} />
            {errors.email && (
              <Form.Control.Feedback type="invalid">{errors.email.message}</Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formFirstName">
            <Form.Label>First Name</Form.Label>
            <Form.Control
              type="text"
              {...register("first_name")}
              isInvalid={!!errors.first_name}
            />
            {errors.first_name && (
              <Form.Control.Feedback type="invalid">
                {errors.first_name.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formLastName">
            <Form.Label>Last Name</Form.Label>
            <Form.Control type="text" {...register("last_name")} isInvalid={!!errors.last_name} />
            {errors.last_name && (
              <Form.Control.Feedback type="invalid">
                {errors.last_name.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsActive">
            <Form.Check
              type="checkbox"
              label="Is Active"
              {...register("is_active")}
              isInvalid={!!errors.is_active}
            />
            {errors.is_active && (
              <Form.Control.Feedback type="invalid">
                {errors.is_active.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsStaff">
            <Form.Check
              type="checkbox"
              label="Is Staff"
              {...register("is_staff")}
              isInvalid={!!errors.is_staff}
            />
            {errors.is_staff && (
              <Form.Control.Feedback type="invalid">
                {errors.is_staff.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsSuperuser">
            <Form.Check
              type="checkbox"
              label="Is Superuser"
              {...register("is_superuser")}
              isInvalid={!!errors.is_superuser}
            />
            {errors.is_superuser && (
              <Form.Control.Feedback type="invalid">
                {errors.is_superuser.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Button variant="primary" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Create User"}
          </Button>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Close
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateUserModal;
