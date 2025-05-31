import axios, { AxiosResponse, AxiosError } from 'axios';
import type { 
  LoginRequest, 
  LoginResponse, 
  RefreshTokenRequest, 
  RefreshTokenResponse,
  User,
  TokenData,
  ApiError
} from '../types/auth';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1', // This will proxy to backend via Vite config
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Token storage keys
const TOKEN_STORAGE_KEY = 'ai_dock_tokens';
const REMEMBER_ME_KEY = 'ai_dock_remember_me';

class AuthService {
  private tokenData: TokenData | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.loadTokensFromStorage();
    this.setupAxiosInterceptors();
  }

  /**
   * Load tokens from storage on service initialization
   */
  private loadTokensFromStorage(): void {
    try {
      const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
      const storage = rememberMe ? localStorage : sessionStorage;
      const storedData = storage.getItem(TOKEN_STORAGE_KEY);
      
      if (storedData) {
        const parsedData = JSON.parse(storedData) as TokenData;
        
        // Check if tokens are still valid
        if (parsedData.expires_at > Date.now()) {
          this.tokenData = parsedData;
          this.scheduleTokenRefresh();
        } else {
          // Clean up expired tokens
          this.clearStoredTokens();
        }
      }
    } catch (error) {
      console.error('Error loading tokens from storage:', error);
      this.clearStoredTokens();
    }
  }

  /**
   * Store tokens in appropriate storage based on remember me preference
   */
  private storeTokens(tokenData: TokenData, rememberMe: boolean): void {
    try {
      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenData));
      localStorage.setItem(REMEMBER_ME_KEY, rememberMe.toString());
      this.tokenData = tokenData;
    } catch (error) {
      console.error('Error storing tokens:', error);
    }
  }

  /**
   * Clear stored tokens from both storages
   */
  private clearStoredTokens(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(REMEMBER_ME_KEY);
    this.tokenData = null;
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Setup axios interceptors for automatic token handling
   */
  private setupAxiosInterceptors(): void {
    // Request interceptor to add auth token
    api.interceptors.request.use(
      (config) => {
        if (this.tokenData?.access_token) {
          config.headers.Authorization = `Bearer ${this.tokenData.access_token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle token expiration
    api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await this.refreshAccessToken();
            // Retry the original request with new token
            if (this.tokenData?.access_token) {
              originalRequest.headers = originalRequest.headers || {};
              originalRequest.headers.Authorization = `Bearer ${this.tokenData.access_token}`;
              return api(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.clearStoredTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );
  }

  /**
   * Schedule automatic token refresh
   */
  private scheduleTokenRefresh(): void {
    if (!this.tokenData) return;

    // Clear existing timer
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    // Schedule refresh 2 minutes before token expires
    const refreshTime = this.tokenData.expires_at - Date.now() - (2 * 60 * 1000);
    
    if (refreshTime > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshAccessToken();
        } catch (error) {
          console.error('Automatic token refresh failed:', error);
          this.clearStoredTokens();
        }
      }, refreshTime);
    }
  }

  /**
   * Login user with username/password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response: AxiosResponse<LoginResponse> = await api.post('/auth/login', credentials);
      const loginData = response.data;
      
      // Calculate token expiration time
      const expiresAt = Date.now() + (loginData.expires_in * 1000);
      
      const tokenData: TokenData = {
        access_token: loginData.access_token,
        refresh_token: loginData.refresh_token,
        expires_at: expiresAt,
        user: loginData.user,
      };
      
      // Store tokens
      this.storeTokens(tokenData, credentials.remember_me || false);
      
      // Schedule automatic refresh
      this.scheduleTokenRefresh();
      
      return loginData;
    } catch (error) {
      const axiosError = error as AxiosError<ApiError>;
      throw new Error(this.extractErrorMessage(axiosError));
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshAccessToken(): Promise<RefreshTokenResponse> {
    if (!this.tokenData?.refresh_token) {
      throw new Error('No refresh token available');
    }

    try {
      const response: AxiosResponse<RefreshTokenResponse> = await api.post('/auth/refresh', {
        refresh_token: this.tokenData.refresh_token,
      });
      
      const refreshData = response.data;
      
      // Update stored token data
      const updatedTokenData: TokenData = {
        ...this.tokenData,
        access_token: refreshData.access_token,
        expires_at: Date.now() + (refreshData.expires_in * 1000),
      };
      
      const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
      this.storeTokens(updatedTokenData, rememberMe);
      this.scheduleTokenRefresh();
      
      return refreshData;
    } catch (error) {
      const axiosError = error as AxiosError<ApiError>;
      this.clearStoredTokens();
      throw new Error(this.extractErrorMessage(axiosError));
    }
  }

  /**
   * Logout user and invalidate tokens
   */
  async logout(): Promise<void> {
    try {
      if (this.tokenData?.access_token) {
        await api.post('/auth/logout');
      }
    } catch (error) {
      // Log error but don't prevent logout
      console.error('Logout API call failed:', error);
    } finally {
      this.clearStoredTokens();
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.get('/auth/me');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError<ApiError>;
      throw new Error(this.extractErrorMessage(axiosError));
    }
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated(): boolean {
    return !!(this.tokenData?.access_token && this.tokenData.expires_at > Date.now());
  }

  /**
   * Get current user data from stored tokens
   */
  getCurrentUserData(): User | null {
    return this.tokenData?.user || null;
  }

  /**
   * Get access token for manual API calls
   */
  getAccessToken(): string | null {
    return this.tokenData?.access_token || null;
  }

  /**
   * Extract error message from API error response
   */
  private extractErrorMessage(error: AxiosError<ApiError>): string {
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === 'string') {
        return detail;
      } else if (Array.isArray(detail)) {
        return detail.map(err => err.msg).join(', ');
      }
    }
    
    if (error.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred';
  }

  /**
   * Check backend connection
   */
  async checkHealth(): Promise<boolean> {
    try {
      await api.get('/auth/health');
      return true;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
