import type { AxiosError } from "axios";

interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

/**
 * Extracts a user-friendly error message from an Axios error or generic Error.
 * Checks for common API error response shapes (detail, message) before falling
 * back to the error's message property.
 */
export function getErrorMessage(error: AxiosError | Error | null | undefined): string | null {
  if (!error) {
    return null;
  }

  // Check if it's an Axios error with response data
  if ("response" in error && error.response?.data) {
    const data = error.response.data as ApiErrorResponse;
    if (data.detail) {
      return data.detail;
    }
    if (data.message) {
      return data.message;
    }
  }

  // Fall back to the error message
  if (error.message) {
    return error.message;
  }

  return "An unexpected error occurred";
}
