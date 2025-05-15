// src/components/layout/NavigationBar.tsx
import React from "react";
import { Container, Image, Nav, Navbar, NavDropdown } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";
import ThemeToggler from "../theme/ThemeToggler";

const NavigationBar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async (): Promise<void> => {
    await logout();
    navigate("/logout"); // Redirect to logout page after logout logic completes
  };

  return (
    <Navbar bg="body-tertiary" expand="lg" sticky="top" className="shadow-sm">
      <Container fluid>
        <Navbar.Brand as={Link} to="/">
          <Image
            src="/brand.svg" // Vite serves from public/ at the root
            alt="Memoria"
            style={{ height: "30px", marginRight: "10px" }} // Adjust scaling as needed
          />
          Memoria
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            {isAuthenticated && (
              <>
                <Nav.Link as={Link} to="/">
                  <i className="bi bi-house-door-fill me-1"></i> Home
                </Nav.Link>
                <Nav.Link as={Link} to="/folders">
                  <i className="bi bi-folder-fill me-1"></i> Folders
                </Nav.Link>
                <Nav.Link as={Link} to="/people">
                  <i className="bi bi-people-fill me-1"></i> People
                </Nav.Link>
                <Nav.Link as={Link} to="/albums">
                  <i className="bi bi-grid me-1"></i> Albums
                </Nav.Link>
              </>
            )}
          </Nav>
          <Nav className="ms-auto align-items-center">
            <div className="me-2">
              {" "}
              {/* Wrapper for Toggler to ensure proper spacing */}
              <ThemeToggler />
            </div>
            {isAuthenticated && user ? (
              <NavDropdown
                title={
                  <>
                    <i className="bi bi-person-circle me-1"></i>
                    {user.first_name || user.username}
                  </>
                }
                id="user-nav-dropdown"
                align="end"
              >
                <NavDropdown.Item as={Link} to="/profile">
                  <i className="bi bi-person-lines-fill me-2"></i> Profile
                </NavDropdown.Item>
                {(user.is_staff || user.is_superuser) && (
                  <NavDropdown.Item as={Link} to="/settings">
                    <i className="bi bi-gear-fill me-2"></i> Settings
                  </NavDropdown.Item>
                )}
                <NavDropdown.Divider />
                <NavDropdown.Item onClick={handleLogout}>
                  <i className="bi bi-box-arrow-right me-2"></i> Logout
                </NavDropdown.Item>
              </NavDropdown>
            ) : (
              <Nav.Link as={Link} to="/login">
                <i className="bi bi-box-arrow-in-right me-1"></i> Login
              </Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavigationBar;
