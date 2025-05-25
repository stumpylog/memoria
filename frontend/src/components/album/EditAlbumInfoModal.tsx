import type { SubmitHandler } from "react-hook-form";

import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { AlbumUpdateInSchema, AlbumWithImagesReadInSchema } from "../../api";

interface EditAlbumInfoModalProps {
  show: boolean;
  onHide: () => void;
  album: AlbumWithImagesReadInSchema | null;
  onSave: (albumId: number, data: AlbumUpdateInSchema) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

interface FormData {
  name: string;
  description: string | null;
}

const EditAlbumInfoModal: React.FC<EditAlbumInfoModalProps> = ({
  show,
  onHide,
  album,
  onSave,
  isLoading,
  error,
}) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isValid },
  } = useForm<FormData>({
    mode: "onChange",
  });

  useEffect(() => {
    if (album && show) {
      reset({
        name: album.name,
        description: album.description || "",
      });
    }
  }, [album, show, reset]);

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    if (!album) return;
    const payload: AlbumUpdateInSchema = {
      //
      name: data.name,
      description: data.description === "" ? null : data.description,
    };
    // Only include fields if they were part of the form or changed
    // For this modal, we are always sending name and description
    await onSave(album.id, payload);
  };

  if (!album) return null;

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Album: {album.name}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form.Group className="mb-3" controlId="albumName">
            <Form.Label>Album Name</Form.Label>
            <Form.Control
              type="text"
              {...register("name", { required: "Album name is required" })}
              isInvalid={!!errors.name}
              disabled={isLoading}
            />
            <Form.Control.Feedback type="invalid">{errors.name?.message}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group className="mb-3" controlId="albumDescription">
            <Form.Label>Description (Optional)</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              {...register("description")}
              disabled={isLoading}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
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
              "Save Changes"
            )}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default EditAlbumInfoModal;
