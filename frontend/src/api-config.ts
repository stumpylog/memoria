import type { InternalAxiosRequestConfig } from "axios";

import { AxiosError } from "axios";

import type { AuthGetCsrfTokenResponse } from "./api/types.gen";

import { client } from "./api/client.gen";

let csrfToken: string | null = null;

// Set the base URL
client.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

const getCookie = (name: string): string | undefined => {
  if (typeof document === "undefined") {
    // Avoid errors in server-side rendering environments
    return undefined;
  }
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(";").shift();
  }
  return undefined;
};

client.instance.interceptors.request.use(
  async (config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> => {
    const isMutatingMethod = ["POST", "PUT", "DELETE", "PATCH"].includes(
      config.method?.toUpperCase() || "",
    );

    if (isMutatingMethod) {
      // Use the getCookie helper function instead of Cookies.get()
      const csrfTokenLocal = getCookie("csrftoken"); // Read the cookie right before the check

      if (csrfToken || csrfTokenLocal) {
        config.headers["X-CSRFToken"] = csrfToken || csrfTokenLocal;
      } else {
        console.warn("Interceptor: CSRF cookie value is undefined. X-CSRFToken header not added.");
      }
    }

    return config;
  },
  (error: AxiosError): Promise<AxiosError> => {
    return Promise.reject(error);
  },
);

// Function to initialize the CSRF token on application startup
export const initializeCsrfToken = async (): Promise<void> => {
  try {
    // Use the generated type for the response data
    const response = await client.instance.get<AuthGetCsrfTokenResponse>("/auth/csrf/", {
      withCredentials: true,
    });
    if (response.data && response.data.csrf_token) {
      csrfToken = response.data.csrf_token;
    }
  } catch (error) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    console.error(
      "Failed to initialize CSRF token:",
      axiosError.response?.data?.detail || axiosError.message,
    );
  }
};
