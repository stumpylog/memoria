// src/components/album/EditAlbumInfoModal.tsx
import type { SubmitHandler } from "react-hook-form";

import { useQuery } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";

import type { AlbumUpdateInSchema, AlbumWithImagesOutSchema, GroupSchemaOut } from "../../api";

import { listGroupsOptions } from "../../api/@tanstack/react-query.gen";
import ThemedSelect from "../common/ThemedSelect";

interface EditAlbumInfoModalProps {
  show: boolean;
  onHide: () => void;
  album: AlbumWithImagesOutSchema | null;
  onSave: (albumId: number, data: AlbumUpdateInSchema) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

interface FormData {
  name: string;
  description: string | null;
  view_group_ids: { value: number; label: string }[];
  edit_group_ids: { value: number; label: string }[];
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
    control,
    formState: { errors, isDirty, isValid },
  } = useForm<FormData>({
    mode: "onChange",
  });

  const {
    data: allGroupsResponse,
    isLoading: isLoadingGroups,
    error: groupsError,
  } = useQuery({
    ...listGroupsOptions(),
  });

  const allGroups: GroupSchemaOut[] = allGroupsResponse ?? [];

  useEffect(() => {
    if (album && show && allGroups) {
      reset({
        name: album.name,
        description: album.description || "",
        view_group_ids:
          album.view_groups?.map((group) => ({ value: group.id, label: group.name })) || [],
        edit_group_ids:
          album.edit_groups?.map((group) => ({ value: group.id, label: group.name })) || [],
      });
    }
  }, [album, show, allGroups, reset]);

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    if (!album) return;
    const payload: AlbumUpdateInSchema = {
      name: data.name,
      description: data.description === "" ? null : data.description,
      view_group_ids: data.view_group_ids.map((group) => group.value),
      edit_group_ids: data.edit_group_ids.map((group) => group.value),
    };
    await onSave(album.id, payload);
  };

  if (!album) return null;

  const groupOptions = allGroups?.map((group) => ({ value: group.id, label: group.name })) || [];

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Album: {album.name}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          {groupsError && (
            <Alert variant="danger">
              Failed to load groups: {groupsError.message || "Unknown error"}
            </Alert>
          )}

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

          {isLoadingGroups ? (
            <div className="text-center">
              <Spinner animation="border" size="sm" /> Loading groups...
            </div>
          ) : (
            <>
              <Form.Group controlId="viewGroupIds" className="mb-3">
                <Form.Label>View Groups</Form.Label>
                <Controller
                  name="view_group_ids"
                  control={control}
                  render={({ field }) => (
                    <ThemedSelect
                      {...field}
                      options={groupOptions}
                      isMulti
                      classNamePrefix="react-select"
                      placeholder="Select groups that can view"
                      isDisabled={isLoading}
                    />
                  )}
                />
                <Form.Text className="text-muted">
                  Users in these groups can view the album. If empty, anyone can view.
                </Form.Text>
              </Form.Group>

              <Form.Group controlId="editGroupIds" className="mb-3">
                <Form.Label>Edit Groups</Form.Label>
                <Controller
                  name="edit_group_ids"
                  control={control}
                  render={({ field }) => (
                    <ThemedSelect
                      {...field}
                      options={groupOptions}
                      isMulti
                      classNamePrefix="react-select"
                      placeholder="Select groups that can edit"
                      isDisabled={isLoading}
                    />
                  )}
                />
                <Form.Text className="text-muted">
                  Users in these groups can edit the album's information and image order. If empty,
                  only staff/superusers can edit.
                </Form.Text>
              </Form.Group>
            </>
          )}
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
