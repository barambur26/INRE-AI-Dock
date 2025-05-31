// Authentication-related TypeScript interfaces
export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  department: string;
  is_active: boolean;
  is_superuser?: boolean;
  is_admin?: boolean;
  role_name?: string;
  department_name?: string;
  role_id?: string;
  department_id?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  user: User;
}

// API Error response
export interface ApiError {
  detail: string | { msg: string; type: string }[];
  status_code?: number;
}
