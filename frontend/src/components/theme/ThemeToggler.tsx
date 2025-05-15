// src/components/theme/ThemeToggler.tsx
import React from "react";
import { Dropdown } from "react-bootstrap";
import { useTheme } from "../../hooks/useTheme"; // Ensure Theme type is exported
import type { Theme } from "../../contexts/ThemeContext";

const ThemeToggler: React.FC = () => {
  const { theme, effectiveTheme, setTheme } = useTheme();

  const handleThemeChange = (eventKey: string | null): void => {
    if (eventKey) {
      const selectedTheme: Theme = eventKey as Theme;
      setTheme(selectedTheme);
    }
  };

  const getThemeIcon = (): string => {
    if (theme === "system") return "bi-circle-half";
    return effectiveTheme === "dark" ? "bi-moon-stars-fill" : "bi-sun-fill";
  };

  return (
    <Dropdown onSelect={handleThemeChange} align="end">
      <Dropdown.Toggle
        variant="outline-secondary"
        id="dropdown-theme-toggler"
        className="d-flex align-items-center"
      >
        <i className={`bi ${getThemeIcon()} me-2`}></i>
        <span className="d-none d-sm-inline">Theme</span>
      </Dropdown.Toggle>
      <Dropdown.Menu>
        <Dropdown.Item eventKey="light" active={theme === "light"}>
          <i className="bi bi-sun-fill me-2"></i> Light
        </Dropdown.Item>
        <Dropdown.Item eventKey="dark" active={theme === "dark"}>
          <i className="bi bi-moon-stars-fill me-2"></i> Dark
        </Dropdown.Item>
        <Dropdown.Item eventKey="system" active={theme === "system"}>
          <i className="bi bi-circle-half me-2"></i> System
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default ThemeToggler;
