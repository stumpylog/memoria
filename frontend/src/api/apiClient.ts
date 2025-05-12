// src/api/apiClient.ts
import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type { User, ApiError, CSRFTokenResponse } from './types'; // User type is still needed for getCurrentUser

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
let csrfToken: string | null = null;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const isMutatingMethod = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase() || '');
    // Only fetch CSRF token if it's not already fetched and the request is a mutating one,
    // and not the CSRF fetch request itself.
    if (isMutatingMethod && !csrfToken && config.url !== '/auth/csrf/') {
      try {
        const tokenResponse = await axios.get<{ csrf_token: string }>(`${API_BASE_URL}/auth/csrf/`, { withCredentials: true });
        if (tokenResponse.data && tokenResponse.data.csrf_token) {
            csrfToken = tokenResponse.data.csrf_token;
        }
        // console.log('CSRF token fetched on demand:', csrfToken);
      } catch (error) {
        console.error('Failed to fetch CSRF token on demand:', error);
      }
    }
    if (isMutatingMethod && csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

export const initializeCsrfToken = async (): Promise<void> => {
  try {
    // console.log('Initializing CSRF token...');
    const response = await apiClient.get<CSRFTokenResponse>('/auth/csrf/');
    if (response.data && response.data.csrf_token) {
         csrfToken = response.data.csrf_token;
        //  console.log('CSRF token initialized from response:', csrfToken);
    } else {
        // console.log('CSRF token initialized (cookie might have been set, no token in response body).');
    }
  } catch (error) {
    const axiosError = error as AxiosError<ApiError>;
    console.error('Failed to initialize CSRF token:', axiosError.response?.data?.detail || axiosError.message);
  }
};

export const apiService = {
  login: async (data: unknown): Promise<void> => { // Changed: Returns Promise<void>
    await apiClient.post('/auth/login/', data);
    // For a 204, there's no data to return. Session cookie should be set.
  },
  logout: async (): Promise<void> => {
    csrfToken = null;
    await apiClient.post('/auth/logout/');
    csrfToken = null;
  },
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/user/profile/');
    return response.data;
  },
};

export default apiClient;
