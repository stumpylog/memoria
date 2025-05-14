// src/components/UserManagement/EditUserModal.tsx
import React, { useState, useEffect } from 'react';
import { Modal, Button, Form, Alert } from 'react-bootstrap';
import type { UserOutSchema, UserUpdateInSchemeWritable } from '../../api';

interface EditUserModalProps {
  show: boolean;
  handleClose: () => void;
  handleSave: (userId: number, userData: UserUpdateInSchemeWritable) => Promise<void>;
  user: UserOutSchema | null;
  loading: boolean;
  error: string | null;
}

const EditUserModal: React.FC<EditUserModalProps> = ({ show, handleClose, handleSave, user, loading, error }) => {
  // State for the form data (can be partial as we only send changed fields)
  const [formData, setFormData] = useState<UserUpdateInSchemeWritable>({});
  // State to store the original user data for comparison
  const [originalUserData, setOriginalUserData] = useState<UserUpdateInSchemeWritable>({});
  // State for the password field (handled separately)
  const [password, setPassword] = useState('');
  // Local error state for modal-specific errors (optional, can use parent error)
  const [localError, setLocalError] = useState<string | null>(null);


  useEffect(() => {
    if (user) {
      // Initialize form data and original data from the user prop
      const initialData: UserUpdateInSchemeWritable = {
        email: user.email ?? null, // Ensure null for comparison if backend sends undefined
        first_name: user.first_name ?? null,
        last_name: user.last_name ?? null,
        // Use ?? false/true for booleans to match form input expectations, but store original boolean/null
        is_active: user.is_active,
        is_staff: user.is_staff,
        is_superuser: user.is_superuser,
      };
      setFormData(initialData);
      setOriginalUserData(initialData); // Store the initial state
      setPassword(''); // Clear password field on user change
      setLocalError(null); // Clear local errors
    } else {
        // Reset form and original data if user becomes null (modal is closed)
        setFormData({});
        setOriginalUserData({});
        setPassword('');
        setLocalError(null);
    }
  }, [user]); // Re-run effect when the user prop changes

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    // Cast to HTMLInputElement to access `checked` safely for checkboxes
    const checked = (e.target as HTMLInputElement).checked;

    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : (value === '' ? null : value), // Treat empty strings for optional fields as null
    });
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      setPassword(e.target.value);
  };


  const handleSubmit = async () => {
    if (!user) {
        setLocalError("No user selected for editing.");
        return;
    }

    setLocalError(null); // Clear previous errors
    // Use a separate loading state if needed, otherwise reuse parent's
    // setModalLoading(true);

    const dataToSave: UserUpdateInSchemeWritable = {};

    // Compare current formData with originalUserData and add changed fields to dataToSave
    const fieldsToCompare: Array<keyof UserUpdateInSchemeWritable> = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser'];

    fieldsToCompare.forEach(field => {
        // Compare values, handling null and undefined consistently
        // Also check if the field exists in formData before comparison
        if (Object.prototype.hasOwnProperty.call(formData, field) && formData[field] !== originalUserData[field]) {
            // The type of formData[field] here is T | null | undefined, where T is string or boolean
            // We need to ensure we assign a type compatible with UserUpdateInSchemeWritable[field]

            // The type of UserUpdateInSchemeWritable[field] is T | null | undefined
            // So, assigning formData[field] should be fine as long as it's not undefined
            if (formData[field] !== undefined) {
                 // This assignment should now be type-compatible
                 // TypeScript knows formData[field] is string | boolean | null here
                 // and dataToSave[field] expects string | null or boolean | null
                 dataToSave[field] = formData[field] as any; // Use 'as any' as a temporary workaround if strict types still complain, but ideally fix the types. Let's try without it first.
            }
        }
    });

    // Include password only if it was entered/changed
    if (password) {
        dataToSave.password = password;
    }

    // If no fields were changed and no password was set, do nothing
    if (Object.keys(dataToSave).length === 0) {
        console.log("No changes detected.");
        handleClose(); // Close modal as nothing needs saving
        return;
    }

    console.log("Saving changes:", dataToSave);

    try {
        // Pass the partial dataToSave object to the handleSave function
        await handleSave(user.id, dataToSave);
        // handleSave in parent should close the modal on success
    } catch (err: any) {
         console.error(`Failed to update user ${user.id}:`, err);
         setLocalError(err.message || `Failed to update user ${user.id}.`);
    } finally {
         // setModalLoading(false);
    }
  };

  return (
    <Modal show={show} onHide={handleClose}>
      <Modal.Header closeButton>
        <Modal.Title>Edit User: {user?.username}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {/* Display either parent error or local error */}
        {(error || localError) && <Alert variant="danger">{error || localError}</Alert>}
        <Form>
           {/* Username is typically not editable via this form */}
           <Form.Group className="mb-3" controlId="formUsernameReadonly">
              <Form.Label>Username</Form.Label>
              <Form.Control type="text" value={user?.username || ''} readOnly disabled />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formPassword">
              <Form.Label>Password (Leave blank to keep current)</Form.Label>
              <Form.Control
                type="password"
                name="password"
                value={password}
                onChange={handlePasswordChange}
                placeholder="Enter new password"
                // Disable password field if parent loading (optional)
                disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formEmail">
              <Form.Label>Email address</Form.Label>
              <Form.Control
                type="email"
                name="email"
                value={formData.email ?? ''}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formFirstName">
              <Form.Label>First Name</Form.Label>
              <Form.Control
                type="text"
                name="first_name"
                value={formData.first_name ?? ''}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formLastName">
              <Form.Label>Last Name</Form.Label>
              <Form.Control
                type="text"
                name="last_name"
                value={formData.last_name ?? ''}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formIsActive">
              <Form.Check
                type="checkbox"
                label="Is Active"
                name="is_active"
                checked={formData.is_active ?? true}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formIsStaff">
              <Form.Check
                type="checkbox"
                label="Is Staff"
                name="is_staff"
                checked={formData.is_staff ?? false}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>

            <Form.Group className="mb-3" controlId="formIsSuperuser">
              <Form.Check
                type="checkbox"
                label="Is Superuser"
                name="is_superuser"
                checked={formData.is_superuser ?? false}
                onChange={handleChange}
                 disabled={loading}
              />
            </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={handleClose} disabled={loading}>
          Close
        </Button>
        <Button variant="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Saving...' : 'Save Changes'}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default EditUserModal;
