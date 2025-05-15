import { AxiosError } from "axios";
import React, { createContext, useCallback, useEffect, useMemo, useState } from "react";

import type { AuthLoginData, UserOutSchema as User } from "../api";
import type { UserProfileOutSchema as UserProfile } from "../api";

import { authLogin, authLogout, userGetMe, userGetMyProfile } from "../api";
import { initializeCsrfToken } from "../api-config";

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  generalApiError: string | null;
  setGeneralApiError: (message: string | null) => void;
  // Use the generated type for login credentials if available, otherwise 'any' or an interface
  login: (credentials: AuthLoginData["body"]) => Promise<boolean>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  fetchUserProfile: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [generalApiError, setGeneralApiErrorState] = useState<string | null>(null);

  // Adapted handleApiError for more general error logging
  const handleApiError = useCallback((err: unknown, context?: string): string => {
    const contextMessage = context ? ` ${context}` : "";
    console.error(`API Error${contextMessage}:`, err); // Log the full error object

    let userFacingMessage = `An unexpected error occurred${contextMessage}.`;

    if (err instanceof AxiosError) {
      // Log Axios specific info
      console.error("Axios Error Details:", {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data, // Log response data, which might contain useful info
      });

      // Provide a slightly more informative message if status or status text is available
      if (err.response) {
        userFacingMessage = `Request failed with status ${err.response.status}${err.response.statusText ? `: ${err.response.statusText}` : ""}${contextMessage}.`;
        // If there's a 'detail' field or similar in your common error response, you could check for it here,
        // but without a specific type, you'd need to access it generally (e.g., `(err.response.data as any)?.detail`)
        // and add checks. For now, we'll keep it simple.
      } else {
        userFacingMessage = `Request failed: ${err.message}${contextMessage}.`;
      }
    } else if (err instanceof Error) {
      userFacingMessage = `An error occurred: ${err.message}${contextMessage}.`;
    }

    // You could return err.message directly if you prefer less generic messages
    return userFacingMessage; // Return a user-friendly message
  }, []);

  const fetchCurrentUser = useCallback(async (): Promise<void> => {
    try {
      const { data } = await userGetMe();
      if (data !== undefined) {
        setUser(data);
      } else {
        // If data is undefined, treat it as no user being logged in
        setUser(null);
      }
    } catch (err) {
      console.error(
        "Failed to fetch current user:",
        handleApiError(err, "when fetching current user"),
      );
      setUser(null);
    }
  }, [handleApiError]);

  const fetchUserProfile = useCallback(async (): Promise<void> => {
    try {
      const { data } = await userGetMyProfile();
      if (data !== undefined) {
        setProfile(data);
      } else {
        setProfile(null);
      }
    } catch (err) {
      console.error(
        "Failed to fetch user profile:",
        handleApiError(err, "when fetching user profile"),
      );
      setProfile(null);
    }
  }, [handleApiError]);

  useEffect(() => {
    const initAuth = async (): Promise<void> => {
      setIsLoading(true);
      await initializeCsrfToken();
      await fetchCurrentUser();
      await fetchUserProfile();
      setIsLoading(false);
    };
    initAuth();
  }, [fetchCurrentUser, fetchUserProfile]);

  const login = useCallback(
    async (credentials: AuthLoginData["body"]): Promise<boolean> => {
      setIsLoading(true);
      setError(null);
      setGeneralApiErrorState(null);
      try {
        await authLogin({
          headers: {
            "Content-Type": "application/json",
          },
          body: credentials,
        });
        await fetchCurrentUser();
        setIsLoading(false);
        return true;
      } catch (err) {
        const errorMessage = handleApiError(err, "during login attempt");
        setError(errorMessage);
        setGeneralApiErrorState(errorMessage);
        setUser(null);
        setIsLoading(false);
        return false;
      }
    },
    [handleApiError, fetchCurrentUser],
  );

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setGeneralApiErrorState(null);
    try {
      await authLogout();
    } catch (err) {
      const errorMessage = handleApiError(err, "during logout");
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

  const contextValue = useMemo(
    () => ({
      user,
      profile,
      isAuthenticated: !!user,
      isLoading,
      error,
      generalApiError,
      setGeneralApiError,
      login,
      logout,
      fetchCurrentUser,
      fetchUserProfile,
    }),
    [
      user,
      profile,
      isLoading,
      error,
      generalApiError,
      setGeneralApiError,
      login,
      logout,
      fetchCurrentUser,
      fetchUserProfile,
    ],
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
};
