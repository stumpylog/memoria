// src/components/UserManagement/CreateUserModal.tsx
import React, { useState } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import type { UserInCreateSchemaWritable } from '../../api';

interface CreateUserModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userData: UserInCreateSchemaWritable) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const CreateUserModal: React.FC<CreateUserModalProps> = ({ show, handleClose, handleSave, loading, error }) => {
  const [formData, setFormData] = useState<UserInCreateSchemaWritable>({
    username: '',
    password: '',
    email: null,
    first_name: null,
    last_name: null,
    is_active: true, // Default to active
    is_staff: false,
    is_superuser: false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async () => {
    // Basic validation
    if (!formData.username || !formData.password) {
      alert('Username and Password are required.');
      return;
    }
    await handleSave(formData);
    // Consider resetting form only on successful save
    // setFormData({ ...initialFormData }); // Define an initial state outside
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Create New User</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        <Form>
          <Form.Group className="mb-3" controlId="formUsername">
            <Form.Label>Username</Form.Label>
            <Form.Control
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formPassword">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formEmail">
            <Form.Label>Email address</Form.Label>
            <Form.Control
              type="email"
              name="email"
              value={formData.email || ''}
              onChange={handleChange}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formFirstName">
            <Form.Label>First Name</Form.Label>
            <Form.Control
              type="text"
              name="first_name"
              value={formData.first_name || ''}
              onChange={handleChange}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formLastName">
            <Form.Label>Last Name</Form.Label>
            <Form.Control
              type="text"
              name="last_name"
              value={formData.last_name || ''}
              onChange={handleChange}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsActive">
            <Form.Check
              type="checkbox"
              label="Is Active"
              name="is_active"
              checked={formData.is_active || false}
              onChange={handleChange}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsStaff">
            <Form.Check
              type="checkbox"
              label="Is Staff"
              name="is_staff"
              checked={formData.is_staff || false}
              onChange={handleChange}
            />
          </Form.Group>

          <Form.Group className="mb-3" controlId="formIsSuperuser">
            <Form.Check
              type="checkbox"
              label="Is Superuser"
              name="is_superuser"
              checked={formData.is_superuser || false}
              onChange={handleChange}
            />
          </Form.Group>

        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Close
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Saving...' : 'Create User'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default CreateUserModal;
