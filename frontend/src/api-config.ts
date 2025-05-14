import { client } from './api/client.gen'; // Adjust the import path
import type { InternalAxiosRequestConfig } from 'axios';
import { AxiosError } from 'axios';
import type { AuthGetCsrfTokenResponse } from './api/types.gen';

let csrfToken: string | null = null;

// Set the base URL
client.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});


client.instance.interceptors.request.use(
  async (config: InternalAxiosRequestConfig): Promise<InternalAxiosRequestConfig> => {
    const isMutatingMethod = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase() || '');

    if (isMutatingMethod) {

      if (csrfToken) { // Check the value of the top-level csrfToken
        config.headers['X-CSRFToken'] = csrfToken;
      } else {
        console.warn('Interceptor: CSRF token is not yet available. X-CSRFToken header not added.');
        return Promise.reject(new AxiosError('CSRF token not available', 'CSRF_TOKEN_MISSING'));
      }
    }

    return config;
  },
  (error: AxiosError): Promise<AxiosError> => {
    return Promise.reject(error);
  }
);

// Function to initialize the CSRF token on application startup
export const initializeCsrfToken = async (): Promise<void> => {
  // console.log('Initializing CSRF token...');
  try {
    // Use the generated type for the response data
    const response = await client.instance.get<AuthGetCsrfTokenResponse>('/auth/csrf/', { withCredentials: true });
    if (response.data && response.data.csrf_token) {
      // Assign the fetched token to the top-level csrfToken variable
      csrfToken = response.data.csrf_token;
      console.log('CSRF token initialized and stored.'); // Optional: Add a log
    } else {
        console.warn('CSRF token endpoint did not return a token.');
    }
  } catch (error) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    console.error('Failed to initialize CSRF token:', axiosError.response?.data?.detail || axiosError.message);
    csrfToken = null;
  }
};
