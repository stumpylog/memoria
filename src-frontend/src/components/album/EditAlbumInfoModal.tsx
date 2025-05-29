// src/components/album/EditAlbumInfoModal.tsx
import type { SubmitHandler } from "react-hook-form";
import type { StylesConfig } from "react-select";

import { useQuery } from "@tanstack/react-query";
import React, { useEffect } from "react";
import { Alert, Button, Form, Modal, Spinner } from "react-bootstrap";
import { Controller, useForm } from "react-hook-form";
import Select from "react-select";

import type { AlbumUpdateInSchema, AlbumWithImagesOutSchema, GroupSchemaOut } from "../../api";

import { listGroups } from "../../api";
import { useTheme } from "../../hooks/useTheme";

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

  const { effectiveTheme } = useTheme();
  const isDarkTheme = effectiveTheme === "dark";

  const {
    data: allGroups,
    isLoading: isLoadingGroups,
    error: groupsError,
  } = useQuery<GroupSchemaOut[], Error>({
    queryKey: ["allGroups"],
    queryFn: async () => {
      const response = await listGroups();
      return response.data || [];
    },
  });

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

  const customStyles: StylesConfig<{ value: number; label: string }, true> = {
    control: (provided, state) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff", // Dark gray for dark, white for light
      borderColor: isDarkTheme ? "#495057" : "#ced4da", // Slightly lighter border for dark
      color: isDarkTheme ? "#f8f9fa" : "#212529", // Light text for dark, dark for light
      "&:hover": {
        borderColor: isDarkTheme ? "#6c757d" : "#80bdff",
      },
      boxShadow: state.isFocused
        ? isDarkTheme
          ? "0 0 0 0.25rem rgba(108, 117, 125, .25)"
          : "0 0 0 0.25rem rgba(0, 123, 255, .25)"
        : "none",
    }),
    input: (provided) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    placeholder: (provided) => ({
      ...provided,
      color: isDarkTheme ? "#adb5bd" : "#6c757d", // Lighter placeholder for dark
    }),
    singleValue: (provided) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    multiValue: (provided) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#495057" : "#e2e6ea", // Darker background for tags in dark theme
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    multiValueLabel: (provided) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
    }),
    multiValueRemove: (provided) => ({
      ...provided,
      color: isDarkTheme ? "#f8f9fa" : "#212529",
      "&:hover": {
        backgroundColor: isDarkTheme ? "#dc3545" : "#dc3545",
        color: "white",
      },
    }),
    menu: (provided) => ({
      ...provided,
      backgroundColor: isDarkTheme ? "#343a40" : "#fff", // Dark gray for dark, white for light
      borderColor: isDarkTheme ? "#495057" : "#ced4da",
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected
        ? isDarkTheme
          ? "#007bff"
          : "#007bff" // Primary blue for selected
        : state.isFocused
          ? isDarkTheme
            ? "#495057"
            : "#e9ecef" // Hover background
          : isDarkTheme
            ? "#343a40"
            : "#fff", // Default background
      color: state.isSelected ? "white" : isDarkTheme ? "#f8f9fa" : "#212529", // Text color
      "&:active": {
        backgroundColor: isDarkTheme ? "#0056b3" : "#0056b3", // Darker blue on active
      },
    }),
  };

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
                    <Select
                      {...field}
                      options={groupOptions}
                      isMulti
                      classNamePrefix="react-select"
                      placeholder="Select groups that can view"
                      isDisabled={isLoading}
                      styles={customStyles}
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
                    <Select
                      {...field}
                      options={groupOptions}
                      isMulti
                      classNamePrefix="react-select"
                      placeholder="Select groups that can edit"
                      isDisabled={isLoading}
                      styles={customStyles}
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
