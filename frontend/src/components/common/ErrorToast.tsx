// src/components/common/ErrorToast.tsx
import React, { useEffect, useState } from "react";
import { Toast, ToastContainer } from "react-bootstrap";
import { useAuth } from "../../hooks/useAuth";

const GlobalErrorToast: React.FC = () => {
  const { generalApiError, setGeneralApiError } = useAuth();
  const [show, setShow] = useState<boolean>(false);

  useEffect(() => {
    if (generalApiError) {
      setShow(true);
    } else {
      setShow(false);
    }
  }, [generalApiError]);

  const handleClose = (): void => {
    setShow(false);
    // Optionally clear the error from context after a delay or on close
    setTimeout(() => {
      setGeneralApiError(null);
    }, 300); // Delay to allow fade out animation
  };

  if (!generalApiError) {
    return null;
  }

  return (
    <ToastContainer position="top-end" className="p-3" style={{ zIndex: 9999 }}>
      <Toast show={show} onClose={handleClose} delay={5000} autohide bg="danger">
        <Toast.Header closeButton={true}>
          <strong className="me-auto">Error</strong>
        </Toast.Header>
        <Toast.Body>{generalApiError}</Toast.Body>
      </Toast>
    </ToastContainer>
  );
};

export default GlobalErrorToast;
