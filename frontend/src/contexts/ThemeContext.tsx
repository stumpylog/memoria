// src/contexts/ThemeContext.tsx
import React, { createContext, useState, useEffect, useMemo, useCallback } from "react";

export type Theme = "light" | "dark" | "system";

interface ThemeContextType {
  theme: Theme;
  effectiveTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const storedTheme = localStorage.getItem("app-theme") as Theme | null;
    return storedTheme || "system";
  });

  const [effectiveTheme, setEffectiveTheme] = useState<"light" | "dark">("light");

  const applyTheme = useCallback((selectedTheme: Theme): "light" | "dark" => {
    let currentEffectiveTheme: "light" | "dark";
    if (selectedTheme === "system") {
      currentEffectiveTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    } else {
      currentEffectiveTheme = selectedTheme;
    }
    document.documentElement.setAttribute("data-bs-theme", currentEffectiveTheme);
    return currentEffectiveTheme;
  }, []); // applyTheme uses no external variables that change across renders, so dependency array is empty

  useEffect(() => {
    const newEffectiveTheme = applyTheme(theme);
    setEffectiveTheme(newEffectiveTheme);
  }, [theme, applyTheme]); // Dependency on theme and the stable applyTheme

  // Listener for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (theme === "system") {
        const newEffectiveTheme = applyTheme("system");
        setEffectiveTheme(newEffectiveTheme);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme, applyTheme]); // Dependency on theme and the stable applyTheme

  // Wrap setTheme in useCallback to make it stable
  const setTheme = useCallback(
    (newTheme: Theme): void => {
      localStorage.setItem("app-theme", newTheme);
      setThemeState(newTheme); // setThemeState is stable, so listing it here doesn't cause issues
    },
    [setThemeState],
  ); // Dependency array includes setThemeState because it's used inside the callback

  const contextValue = useMemo(
    () => ({
      theme,
      effectiveTheme,
      setTheme, // This is now the stable function wrapped by useCallback
    }),
    [theme, effectiveTheme, setTheme],
  ); // Now setTheme is a stable dependency

  return <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>;
};
