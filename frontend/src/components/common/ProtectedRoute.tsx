// src/components/common/ProtectedRoute.tsx
import React from "react";
import { Spinner } from "react-bootstrap"; // For loading state
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

interface ProtectedRouteProps {
  // Future: Add role/permission checks here
  // allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = (/* { allowedRoles } */) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    // Show a loading spinner or a blank page while auth state is being determined
    return (
      <div
        className="d-flex justify-content-center align-items-center"
        style={{ height: "100vh" }}
      >
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect them to the /login page, but save the current location they were
    // trying to go to when they were redirected. This allows us to send them
    // along to that page after they login, which is a nicer user experience
    // than dropping them off on the home page.
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Future permission checks can go here:
  // const { user } = useAuth();
  // if (allowedRoles && user && !allowedRoles.some(role => user.roles.includes(role))) {
  //   return <Navigate to="/unauthorized" replace />;
  // }

  return <Outlet />; // Render the child route component
};

export default ProtectedRoute;
