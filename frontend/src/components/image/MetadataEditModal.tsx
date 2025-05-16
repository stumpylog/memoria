// src/components/image/MetadataEditModal.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { ImageMetadataSchemaOut, ImageMetadataUpdateSchemaIn } from "../../api";

import { imageUpdateMetadata } from "../../api";

interface MetadataEditModalProps {
  show: boolean;
  onHide: () => void;
  imageId: number;
  currentMetadata: ImageMetadataSchemaOut;
}

const MetadataEditModal: React.FC<MetadataEditModalProps> = ({
  show,
  onHide,
  imageId,
  currentMetadata,
}) => {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ImageMetadataUpdateSchemaIn>({
    defaultValues: {
      title: currentMetadata?.title || null,
      description: currentMetadata?.description || null,
    },
  });

  // Reset form when modal opens with new data
  React.useEffect(() => {
    if (show) {
      reset({
        title: currentMetadata?.title || null,
        description: currentMetadata?.description || null,
      });
    }
  }, [reset, show, currentMetadata]);

  const updateMetadataMutation = useMutation({
    mutationFn: (data: ImageMetadataUpdateSchemaIn) =>
      imageUpdateMetadata({
        path: { image_id: imageId },
        body: data,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["metadata", imageId] });
      onHide();
    },
    onError: (err) => {
      console.error("Failed to update metadata:", err);
    },
  });

  const onSubmit = (data: ImageMetadataUpdateSchemaIn) => {
    // Convert empty strings to null
    const sanitizedData = {
      ...data,
      title: data.title === "" ? null : data.title,
      description: data.description === "" ? null : data.description,
    };
    updateMetadataMutation.mutate(sanitizedData);
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Image Details</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {updateMetadataMutation.isError && (
            <div className="alert alert-danger">
              Failed to update image details. Please try again.
            </div>
          )}

          <div className="mb-3">
            <h6>Current Title:</h6>
            <p className="text-muted">{currentMetadata?.title || "Untitled Image"}</p>

            <h6>Current Description:</h6>
            <p className="text-muted">
              {currentMetadata?.description || (
                <span className="fst-italic">No description set</span>
              )}
            </p>
          </div>

          <Form.Group className="mb-3">
            <Form.Label>Title</Form.Label>
            <Form.Control
              type="text"
              placeholder="Image title"
              {...register("title", {
                maxLength: {
                  value: 100,
                  message: "Title must be 100 characters or less",
                },
              })}
              isInvalid={!!errors.title}
            />
            {errors.title && (
              <Form.Control.Feedback type="invalid">{errors.title.message}</Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Image description"
              {...register("description", {
                maxLength: {
                  value: 500,
                  message: "Description must be 500 characters or less",
                },
              })}
              isInvalid={!!errors.description}
            />
            {errors.description && (
              <Form.Control.Feedback type="invalid">
                {errors.description.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isSubmitting || updateMetadataMutation.isPending}
          >
            {isSubmitting || updateMetadataMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default MetadataEditModal;
