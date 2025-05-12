// src/api/types.ts

export interface Profile {
  default_items_per_page: number;
  timezone: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  profile: Profile;
}

// For Pydantic error responses
export interface ApiErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ApiError {
  detail?: string | ApiErrorDetail[];
}

export interface CSRFTokenResponse {
  csrf_token: string;
}
