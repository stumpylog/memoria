// src/contexts/AuthContext.tsx
import React, { createContext, useState, useEffect, useMemo, useCallback } from 'react';
import { apiService, initializeCsrfToken } from '../api/apiClient';
import type { User, ApiError } from '../api/types';
import { AxiosError } from 'axios';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  generalApiError: string | null;
  setGeneralApiError: (message: string | null) => void;
  login: (credentials: unknown) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>; // Keep as Promise<void> - its job is to set state
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [generalApiError, setGeneralApiErrorState] = useState<string | null>(null);

  const handleApiError = useCallback((err: unknown, context?: string): string => {
    let errorMessage = `An unexpected error occurred${context ? ` ${context}` : ''}.`;
    if (err instanceof AxiosError) {
      const apiError = err.response?.data as ApiError;
      if (apiError?.detail) {
        if (typeof apiError.detail === 'string') {
          errorMessage = apiError.detail;
        } else if (Array.isArray(apiError.detail)) {
          errorMessage = apiError.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join('; ');
        }
      } else if (err.response?.statusText && (err.response.status === 401 || err.response.status === 403) ) {
        errorMessage = `Authentication failed: ${err.response.statusText}`;
      }
       else if (err.message) {
        errorMessage = err.message;
      }
    } else if (err instanceof Error) {
      errorMessage = err.message;
    }
    return errorMessage;
  }, []);

  const fetchCurrentUser = useCallback(async (): Promise<void> => {
    // This function is called on initial load and after login.
    // It should not manage setIsLoading by itself if part of a larger flow like login() or initAuth().
    try {
      const userData = await apiService.getCurrentUser();
      setUser(userData); // This will make isAuthenticated true if userData is valid
    } catch (err) {
      console.log(err);
      setUser(null); // Crucial: if fetching user fails, ensure user is null
    }
  }, [/* setUser is stable */]);

  useEffect(() => {
    const initAuth = async (): Promise<void> => {
      setIsLoading(true); // Start loading for initial auth check
      await initializeCsrfToken();
      await fetchCurrentUser(); // Attempt to fetch user (sets user state)
      setIsLoading(false); // Finish loading for initial auth check
    };
    initAuth();
  }, [fetchCurrentUser]);


  const login = useCallback(async (credentials: unknown): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    setGeneralApiErrorState(null);
    try {
      await apiService.login(credentials); // Call login, backend sets session cookie (e.g., 204 response)
      await fetchCurrentUser();         // Now, fetch the user details using the new session

      // After fetchCurrentUser, the `user` state (and thus `isAuthenticated`) will be updated.
      // The `isLoading` state is also managed.
      // The `useEffect` in `LoginPage` will react to these state changes.
      setIsLoading(false); // Login process (API calls) complete

      // To determine actual success for the boolean return, we would need to check the user state here.
      // However, state updates are async. Instead, we rely on the reactive flow.
      // If fetchCurrentUser fails and sets user to null, isAuthenticated remains false.
      // This boolean mainly indicates the POST /login didn't throw an immediate error.
      return true; // Indicates POST /login was successful (2xx). User state will determine actual auth.
    } catch (err) {
      // This error is likely from apiService.login() itself (e.g., 400 Bad Request, 500)
      // or if fetchCurrentUser() re-threw an error (which it currently doesn't).
      const errorMessage = handleApiError(err, 'during login attempt');
      setError(errorMessage); // For the login form
      setGeneralApiErrorState(errorMessage); // For a toast
      setUser(null); // Ensure user state is cleared
      setIsLoading(false);
      return false;
    }
  }, [handleApiError, fetchCurrentUser /* Dependencies like setIsLoading, setUser, etc., are stable */]);

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setGeneralApiErrorState(null);
    try {
      await apiService.logout();
    } catch (err) {
      const errorMessage = handleApiError(err, 'during logout');
      setGeneralApiErrorState(errorMessage);
      console.error("Logout failed:", errorMessage);
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  }, [handleApiError]);

  const setGeneralApiError = useCallback((message: string | null): void => {
    setGeneralApiErrorState(message);
  }, []);

  const contextValue = useMemo(() => ({
    user,
    isAuthenticated: !!user, // This is key for redirection
    isLoading,
    error,
    generalApiError,
    setGeneralApiError,
    login,
    logout,
    fetchCurrentUser,
  }), [
    user, // `isAuthenticated` depends directly on `user`
    isLoading,
    error,
    generalApiError,
    setGeneralApiError,
    login,
    logout,
    fetchCurrentUser
  ]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
