import type { UseFormReturn } from "react-hook-form";

import React from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";

interface FormModalProps<TFormData> {
  show: boolean;
  onHide: () => void;
  title: string;
  size?: "sm" | "lg" | "xl";
  isLoading: boolean;
  error: string | null;
  submitLabel?: string;
  children: React.ReactNode;
  form: UseFormReturn<TFormData>;
  onSubmit: (data: TFormData) => void | Promise<void>;
}

/**
 * A reusable modal wrapper for forms that integrates with React Hook Form.
 * Handles loading states, error alerts, and form submission.
 *
 * @example
 * const form = useForm<FormData>();
 * <FormModal
 *   show={show}
 *   onHide={handleClose}
 *   title="Edit Item"
 *   isLoading={mutation.isPending}
 *   error={errorMessage}
 *   form={form}
 *   onSubmit={handleSubmit}
 * >
 *   <Form.Group>
 *     <Form.Label>Name</Form.Label>
 *     <Form.Control {...form.register("name")} />
 *   </Form.Group>
 * </FormModal>
 */
function FormModal<TFormData>({
  show,
  onHide,
  title,
  size,
  isLoading,
  error,
  submitLabel = "Save Changes",
  children,
  form,
  onSubmit,
}: FormModalProps<TFormData>) {
  const { handleSubmit, formState } = form;
  const { isDirty, isValid } = formState;

  return (
    <Modal show={show} onHide={onHide} size={size} centered>
      <Modal.Header closeButton>
        <Modal.Title>{title}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          {children}
        </Modal.Body>
        <Modal.Footer>
          {isDirty && !isLoading && <small className="text-muted me-auto">Unsaved changes</small>}
          <Button variant="secondary" onClick={onHide} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" disabled={isLoading || !isDirty || !isValid}>
            {isLoading ? (
              <>
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
                {" Saving..."}
              </>
            ) : (
              submitLabel
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}

export default FormModal;
