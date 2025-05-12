// src/contexts/ThemeContext.tsx
import React, { createContext, useState, useEffect, useMemo, useCallback } from 'react';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  effectiveTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const storedTheme = localStorage.getItem('app-theme') as Theme | null;
    return storedTheme || 'system';
  });

  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light');

  const applyTheme = useCallback((selectedTheme: Theme): 'light' | 'dark' => {
    let currentEffectiveTheme: 'light' | 'dark';
    if (selectedTheme === 'system') {
      currentEffectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } else {
      currentEffectiveTheme = selectedTheme;
    }
    document.documentElement.setAttribute('data-bs-theme', currentEffectiveTheme);
    return currentEffectiveTheme;
  }, []);

  useEffect(() => {
    const newEffectiveTheme = applyTheme(theme);
    setEffectiveTheme(newEffectiveTheme);
  }, [theme, applyTheme]);

  // Listener for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        const newEffectiveTheme = applyTheme('system');
        setEffectiveTheme(newEffectiveTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, applyTheme]);

  const setTheme = (newTheme: Theme): void => {
    localStorage.setItem('app-theme', newTheme);
    setThemeState(newTheme);
  };

  const contextValue = useMemo(() => ({
    theme,
    effectiveTheme,
    setTheme,
  }), [theme, effectiveTheme, setTheme]);

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};
