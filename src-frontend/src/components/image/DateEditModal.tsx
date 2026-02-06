// src/components/image/DateEditModal.tsx

import { useMutation, useQueryClient } from "@tanstack/react-query";
import React from "react";
import { Button, Form, Modal } from "react-bootstrap";
import { useForm } from "react-hook-form";

import type { ImageDateSchemaOut, ImageDateUpdateSchemaIn } from "../../api";

import { imageUpdateDateMutation } from "../../api/@tanstack/react-query.gen";

interface DateEditModalProps {
  show: boolean;
  onHide: () => void;
  imageId: number;
  currentDate: ImageDateSchemaOut | null;
  onDateUpdated: () => void;
}

// Parse display format (YYYY-MM-DD or YYYY-XX-YY) to actual date value
const parseDisplayDate = (dateInfo: ImageDateSchemaOut | null): string => {
  if (!dateInfo || !dateInfo.comparison_date) return "";

  // If date is already in ISO format or doesn't contain MM/DD placeholders, return as is
  if (!dateInfo.comparison_date.includes("MM") && !dateInfo.comparison_date.includes("DD")) {
    return dateInfo.comparison_date;
  }

  try {
    // Parse from display format with placeholders
    const parts = dateInfo.comparison_date.split("-");
    if (parts.length !== 3) return dateInfo.comparison_date;

    const year = parts[0];
    const month = parts[1] === "MM" ? "01" : parts[1];
    const day = parts[2] === "DD" ? "01" : parts[2];

    return `${year}-${month}-${day}`;
  } catch (e) {
    return dateInfo.comparison_date;
  }
};

const DateEditModal: React.FC<DateEditModalProps> = ({
  show,
  onHide,
  imageId,
  currentDate,
  onDateUpdated,
}) => {
  // Destructure the new prop
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ImageDateUpdateSchemaIn>({
    defaultValues: {
      date: parseDisplayDate(currentDate),
      day_valid: currentDate?.day_valid || false,
      month_valid: currentDate?.month_valid || false,
    },
  });

  // Reset form when modal opens with new data
  React.useEffect(() => {
    if (show) {
      reset({
        date: parseDisplayDate(currentDate),
        day_valid: currentDate?.day_valid || false,
        month_valid: currentDate?.month_valid || false,
      });
    }
  }, [reset, show, currentDate]);

  const updateDateMutation = useMutation({
    ...imageUpdateDateMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["date", imageId] });
      onHide();
      onDateUpdated(); // Call the callback on success
    },
    onError: (err) => {
      console.error("Failed to update date:", err);
    },
  });

  const onSubmit = (data: ImageDateUpdateSchemaIn) => {
    updateDateMutation.mutate({
      path: { image_id: imageId },
      body: data,
    });
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>Edit Date Information</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <Modal.Body>
          {updateDateMutation.isError && (
            <div className="alert alert-danger">
              Failed to update date information. Please try again.
            </div>
          )}

          <p className="text-muted mb-3">
            {currentDate && currentDate.comparison_date
              ? `Current date: ${parseDisplayDate(currentDate)}`
              : "No date currently set"}
          </p>

          <Form.Group className="mb-3">
            <Form.Label>Date</Form.Label>
            <Form.Control
              type="text"
              placeholder="YYYY-MM-DD"
              {...register("date", {
                required: "Date is required",
              })}
              isInvalid={!!errors.date}
            />
            <Form.Text className="text-muted">Enter a date in YYYY-MM-DD format</Form.Text>
            {errors.date && (
              <Form.Control.Feedback type="invalid">{errors.date.message}</Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check type="checkbox" label="Day is accurate" {...register("day_valid")} />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Check type="checkbox" label="Month is accurate" {...register("month_valid")} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            disabled={isSubmitting || updateDateMutation.isPending}
          >
            {isSubmitting || updateDateMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

export default DateEditModal;
