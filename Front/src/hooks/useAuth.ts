import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/authService';
import type { User, LoginRequest, AuthState } from '../types/auth';

// Auth context interface
interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider props
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * Wraps the app to provide authentication state and functions
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const queryClient = useQueryClient();

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      setAuthState(prev => ({ ...prev, isLoading: true }));
      
      try {
        if (authService.isAuthenticated()) {
          const userData = authService.getCurrentUserData();
          if (userData) {
            setAuthState({
              user: userData,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            // Try to fetch fresh user data
            const freshUserData = await authService.getCurrentUser();
            setAuthState({
              user: freshUserData,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          }
        } else {
          setAuthState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setAuthState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Authentication failed',
        });
      }
    };

    initializeAuth();
  }, []);

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const response = await authService.login(credentials);
      return response;
    },
    onSuccess: (response) => {
      setAuthState({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      queryClient.invalidateQueries();
    },
    onError: (error: Error) => {
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message,
      }));
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await authService.logout();
    },
    onSuccess: () => {
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
      queryClient.clear();
    },
    onError: (error: Error) => {
      // Still clear local state even if logout API fails
      setAuthState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: error.message,
      });
      queryClient.clear();
    },
  });

  // User refresh query
  const { refetch: refetchUser } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authService.getCurrentUser(),
    enabled: false, // Only fetch when explicitly called
    onSuccess: (userData) => {
      setAuthState(prev => ({
        ...prev,
        user: userData,
        isAuthenticated: true,
        error: null,
      }));
    },
    onError: (error: Error) => {
      console.error('Failed to refresh user data:', error);
      setAuthState(prev => ({
        ...prev,
        error: error.message,
      }));
    },
  });

  // Wrapped functions
  const login = useCallback(async (credentials: LoginRequest) => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
    await loginMutation.mutateAsync(credentials);
  }, [loginMutation]);

  const logout = useCallback(async () => {
    setAuthState(prev => ({ ...prev, isLoading: true }));
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  const refreshUser = useCallback(async () => {
    await refetchUser();
  }, [refetchUser]);

  const clearError = useCallback(() => {
    setAuthState(prev => ({ ...prev, error: null }));
  }, []);

  const contextValue: AuthContextType = {
    ...authState,
    login,
    logout,
    refreshUser,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 * Must be used within AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook for login functionality with form handling
 */
export function useLogin() {
  const { login, isLoading, error } = useAuth();
  
  return {
    login,
    isLoading,
    error,
  };
}

/**
 * Hook for logout functionality
 */
export function useLogout() {
  const { logout, isLoading } = useAuth();
  
  return {
    logout,
    isLoading,
  };
}

/**
 * Hook to check if user has specific role
 */
export function useRole() {
  const { user } = useAuth();
  
  const hasRole = useCallback((role: string) => {
    return user?.role === role;
  }, [user]);

  const isAdmin = useCallback(() => {
    return hasRole('admin');
  }, [hasRole]);

  return {
    userRole: user?.role || null,
    hasRole,
    isAdmin,
  };
}

export default useAuth;
