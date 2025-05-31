import axios, { AxiosResponse, AxiosError } from 'axios';
import type {
  User,
  UserCreate,
  UserUpdate,
  UserListResponse,
  Department,
  DepartmentCreate,
  DepartmentUpdate,
  DepartmentListResponse,
  Role,
  RoleCreate,
  RoleUpdate,
  RoleListResponse,
  LLMConfiguration,
  LLMConfigCreate,
  LLMConfigUpdate,
  LLMConfigListResponse,
  LLMConfigurationJSONInput,
  LLMConfigValidationResponse,
  BulkLLMConfigUpdate,
  BulkLLMConfigResponse,
  LLMConfigStats,
  ProvidersResponse,
  LLMConfigUsageSummary,
  AdminStats,
  AvailablePermissionsResponse,
  UserFilters,
  BulkUserUpdate,
  BulkResponse,
  ApiResponse,
  // Quota types
  Quota,
  QuotaCreate,
  QuotaUpdate,
  QuotaListResponse,
  QuotaFilters,
  QuotaTemplatesResponse,
  QuotaOverviewStats,
  DepartmentQuotaSummary,
  QuotaAlertsResponse,
  BulkQuotaCreate,
  BulkQuotaUpdate,
  BulkQuotaResponse,
  QuotaResetRequest,
  QuotaResetResponse,
  QuotaEnforcement
} from '../types/admin';

// Use the same axios instance as auth service
const api = axios.create({
  baseURL: '/api/v1', // This will proxy to backend via Vite config
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // Longer timeout for admin operations
});

// Add token interceptor (similar to auth service)
api.interceptors.request.use(
  (config) => {
    // Get token from auth service or storage
    const token = getStoredToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Helper to get stored token
function getStoredToken(): string | null {
  try {
    const rememberMe = localStorage.getItem('ai_dock_remember_me') === 'true';
    const storage = rememberMe ? localStorage : sessionStorage;
    const storedData = storage.getItem('ai_dock_tokens');
    
    if (storedData) {
      const parsedData = JSON.parse(storedData);
      return parsedData.access_token || null;
    }
  } catch (error) {
    console.error('Error getting stored token:', error);
  }
  return null;
}

// Helper to extract error messages
function extractErrorMessage(error: AxiosError<any>): string {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    if (typeof detail === 'string') {
      return detail;
    } else if (Array.isArray(detail)) {
      return detail.map((err: any) => err.msg || err.message || err).join(', ');
    }
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
}

class AdminService {
  // User Management
  async getUsers(filters: UserFilters = {}): Promise<UserListResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.page !== undefined) params.append('skip', ((filters.page - 1) * (filters.limit || 100)).toString());
      if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.role_id) params.append('role_id', filters.role_id);
      if (filters.department_id) params.append('department_id', filters.department_id);
      if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString());
      
      const response: AxiosResponse<UserListResponse> = await api.get(`/admin/users?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUser(userId: string): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.get(`/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createUser(userData: UserCreate): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.post('/admin/users/', userData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateUser(userId: string, userData: UserUpdate): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.put(`/admin/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deleteUser(userId: string): Promise<void> {
    try {
      await api.delete(`/admin/users/${userId}`);
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async activateUser(userId: string): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.post(`/admin/users/${userId}/activate`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deactivateUser(userId: string): Promise<User> {
    try {
      const response: AxiosResponse<User> = await api.post(`/admin/users/${userId}/deactivate`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async resetUserPassword(userId: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post(
        `/admin/users/${userId}/reset-password?new_password=${encodeURIComponent(newPassword)}`
      );
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async bulkUpdateUsers(bulkData: BulkUserUpdate): Promise<BulkResponse> {
    try {
      const response: AxiosResponse<BulkResponse> = await api.post('/admin/users/bulk-update', bulkData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // Department Management
  async getDepartments(): Promise<DepartmentListResponse> {
    try {
      const response: AxiosResponse<DepartmentListResponse> = await api.get('/admin/departments/');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getDepartment(departmentId: string): Promise<Department> {
    try {
      const response: AxiosResponse<Department> = await api.get(`/admin/departments/${departmentId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createDepartment(departmentData: DepartmentCreate): Promise<Department> {
    try {
      const response: AxiosResponse<Department> = await api.post('/admin/departments/', departmentData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateDepartment(departmentId: string, departmentData: DepartmentUpdate): Promise<Department> {
    try {
      const response: AxiosResponse<Department> = await api.put(`/admin/departments/${departmentId}`, departmentData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deleteDepartment(departmentId: string): Promise<void> {
    try {
      await api.delete(`/admin/departments/${departmentId}`);
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getDepartmentUsers(departmentId: string): Promise<{ department: Department; users: User[]; total_users: number }> {
    try {
      const response = await api.get(`/admin/departments/${departmentId}/users`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async assignUserToDepartment(departmentId: string, userId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post(`/admin/departments/${departmentId}/users/${userId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async removeUserFromDepartment(departmentId: string, userId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.delete(`/admin/departments/${departmentId}/users/${userId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // Role Management
  async getRoles(): Promise<RoleListResponse> {
    try {
      const response: AxiosResponse<RoleListResponse> = await api.get('/admin/roles/');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getRole(roleId: string): Promise<Role> {
    try {
      const response: AxiosResponse<Role> = await api.get(`/admin/roles/${roleId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createRole(roleData: RoleCreate): Promise<Role> {
    try {
      const response: AxiosResponse<Role> = await api.post('/admin/roles/', roleData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateRole(roleId: string, roleData: RoleUpdate): Promise<Role> {
    try {
      const response: AxiosResponse<Role> = await api.put(`/admin/roles/${roleId}`, roleData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deleteRole(roleId: string): Promise<void> {
    try {
      await api.delete(`/admin/roles/${roleId}`);
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getRoleUsers(roleId: string): Promise<{ role: Role; users: User[]; total_users: number }> {
    try {
      const response = await api.get(`/admin/roles/${roleId}/users`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async assignRoleToUser(roleId: string, userId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post(`/admin/roles/${roleId}/users/${userId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async removeRoleFromUser(roleId: string, userId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.delete(`/admin/roles/${roleId}/users/${userId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getAvailablePermissions(): Promise<AvailablePermissionsResponse> {
    try {
      const response: AxiosResponse<AvailablePermissionsResponse> = await api.get('/admin/roles/permissions');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async addPermissionToRole(roleId: string, permission: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post(
        `/admin/roles/${roleId}/permissions?permission=${encodeURIComponent(permission)}`
      );
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async removePermissionFromRole(roleId: string, permission: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.delete(
        `/admin/roles/${roleId}/permissions/${encodeURIComponent(permission)}`
      );
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // LLM Configuration Management
  async getLLMConfigurations(filters: {
    skip?: number;
    limit?: number;
    enabled_only?: boolean;
    provider?: string;
    search?: string;
  } = {}): Promise<LLMConfigListResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
      if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
      if (filters.enabled_only !== undefined) params.append('enabled_only', filters.enabled_only.toString());
      if (filters.provider) params.append('provider', filters.provider);
      if (filters.search) params.append('search', filters.search);
      
      const response: AxiosResponse<LLMConfigListResponse> = await api.get(`/admin/llm-configurations?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getLLMConfiguration(configId: string): Promise<LLMConfiguration> {
    try {
      const response: AxiosResponse<LLMConfiguration> = await api.get(`/admin/llm-configurations/${configId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createLLMConfiguration(configData: LLMConfigCreate): Promise<LLMConfiguration> {
    try {
      const response: AxiosResponse<LLMConfiguration> = await api.post('/admin/llm-configurations/', configData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateLLMConfiguration(configId: string, configData: LLMConfigUpdate): Promise<LLMConfiguration> {
    try {
      const response: AxiosResponse<LLMConfiguration> = await api.put(`/admin/llm-configurations/${configId}`, configData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deleteLLMConfiguration(configId: string): Promise<void> {
    try {
      await api.delete(`/admin/llm-configurations/${configId}`);
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async enableLLMConfiguration(configId: string): Promise<LLMConfiguration> {
    try {
      const response: AxiosResponse<LLMConfiguration> = await api.post(`/admin/llm-configurations/${configId}/enable`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async disableLLMConfiguration(configId: string): Promise<LLMConfiguration> {
    try {
      const response: AxiosResponse<LLMConfiguration> = await api.post(`/admin/llm-configurations/${configId}/disable`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async validateLLMConfigJSON(jsonInput: LLMConfigurationJSONInput): Promise<LLMConfigValidationResponse> {
    try {
      const response: AxiosResponse<LLMConfigValidationResponse> = await api.post('/admin/llm-configurations/validate-json', jsonInput);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async importLLMConfigJSON(jsonInput: LLMConfigurationJSONInput, validateOnly: boolean = false): Promise<BulkLLMConfigResponse> {
    try {
      const params = validateOnly ? '?validate_only=true' : '';
      const response: AxiosResponse<BulkLLMConfigResponse> = await api.post(`/admin/llm-configurations/import-json${params}`, jsonInput);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async bulkUpdateLLMConfigurations(bulkData: BulkLLMConfigUpdate): Promise<BulkLLMConfigResponse> {
    try {
      const response: AxiosResponse<BulkLLMConfigResponse> = await api.post('/admin/llm-configurations/bulk-update', bulkData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async bulkEnableLLMConfigurations(configIds: string[]): Promise<BulkLLMConfigResponse> {
    try {
      const response: AxiosResponse<BulkLLMConfigResponse> = await api.post('/admin/llm-configurations/bulk-enable', configIds);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async bulkDisableLLMConfigurations(configIds: string[]): Promise<BulkLLMConfigResponse> {
    try {
      const response: AxiosResponse<BulkLLMConfigResponse> = await api.post('/admin/llm-configurations/bulk-disable', configIds);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getLLMConfigStats(): Promise<LLMConfigStats> {
    try {
      const response: AxiosResponse<LLMConfigStats> = await api.get('/admin/llm-configurations/stats/overview');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getAvailableProviders(): Promise<ProvidersResponse> {
    try {
      const response: AxiosResponse<ProvidersResponse> = await api.get('/admin/llm-configurations/providers');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getLLMConfigUsageSummary(configId: string): Promise<LLMConfigUsageSummary> {
    try {
      const response: AxiosResponse<LLMConfigUsageSummary> = await api.get(`/admin/llm-configurations/${configId}/usage-summary`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getEnabledLLMConfigurations(provider?: string): Promise<{ configurations: LLMConfiguration[]; total: number; provider_filter?: string }> {
    try {
      const params = provider ? `?provider=${encodeURIComponent(provider)}` : '';
      const response = await api.get(`/admin/llm-configurations/models/enabled${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // Admin Statistics
  async getAdminStats(): Promise<AdminStats> {
    try {
      const response: AxiosResponse<AdminStats> = await api.get('/admin/stats');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // System Operations
  async initializeDefaultData(): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post('/admin/initialize');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async checkAdminHealth(): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.get('/admin/health');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // Quota Management
  async getQuotas(filters: QuotaFilters & {
    skip?: number;
    limit?: number;
  } = {}): Promise<QuotaListResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
      if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
      if (filters.department_id) params.append('department_id', filters.department_id);
      if (filters.llm_config_id) params.append('llm_config_id', filters.llm_config_id);
      if (filters.enforcement_mode) params.append('enforcement_mode', filters.enforcement_mode);
      if (filters.exceeded_only !== undefined) params.append('exceeded_only', filters.exceeded_only.toString());
      if (filters.warning_only !== undefined) params.append('warning_only', filters.warning_only.toString());
      
      const response: AxiosResponse<QuotaListResponse> = await api.get(`/admin/quotas?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getQuota(quotaId: string): Promise<Quota> {
    try {
      const response: AxiosResponse<Quota> = await api.get(`/admin/quotas/${quotaId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createQuota(quotaData: QuotaCreate): Promise<Quota> {
    try {
      const response: AxiosResponse<Quota> = await api.post('/admin/quotas/', quotaData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateQuota(quotaId: string, quotaData: QuotaUpdate): Promise<Quota> {
    try {
      const response: AxiosResponse<Quota> = await api.put(`/admin/quotas/${quotaId}`, quotaData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async deleteQuota(quotaId: string): Promise<void> {
    try {
      await api.delete(`/admin/quotas/${quotaId}`);
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getQuotaOverview(): Promise<QuotaOverviewStats> {
    try {
      const response: AxiosResponse<QuotaOverviewStats> = await api.get('/admin/quotas/overview');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getQuotaAlerts(limit: number = 50): Promise<QuotaAlertsResponse> {
    try {
      const response: AxiosResponse<QuotaAlertsResponse> = await api.get(`/admin/quotas/alerts?limit=${limit}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getQuotaTemplates(): Promise<QuotaTemplatesResponse> {
    try {
      const response: AxiosResponse<QuotaTemplatesResponse> = await api.get('/admin/quotas/templates');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getDepartmentQuotas(departmentId: string): Promise<Quota[]> {
    try {
      const response: AxiosResponse<Quota[]> = await api.get(`/admin/quotas/department/${departmentId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getDepartmentQuotaSummary(departmentId: string): Promise<DepartmentQuotaSummary> {
    try {
      const response: AxiosResponse<DepartmentQuotaSummary> = await api.get(`/admin/quotas/department/${departmentId}/summary`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async createBulkQuotas(bulkData: BulkQuotaCreate): Promise<BulkQuotaResponse> {
    try {
      const response: AxiosResponse<BulkQuotaResponse> = await api.post('/admin/quotas/bulk', bulkData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateBulkQuotas(bulkData: BulkQuotaUpdate): Promise<BulkQuotaResponse> {
    try {
      const response: AxiosResponse<BulkQuotaResponse> = await api.put('/admin/quotas/bulk', bulkData);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async resetQuotas(resetRequest: QuotaResetRequest): Promise<QuotaResetResponse> {
    try {
      const response: AxiosResponse<QuotaResetResponse> = await api.post('/admin/quotas/reset', resetRequest);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async checkQuotaLimits(
    departmentId: string, 
    llmConfigId: string, 
    tokensRequested: number = 0
  ): Promise<{
    can_proceed: boolean;
    message: string;
    quota_info: any;
    department_id: string;
    llm_config_id: string;
    tokens_requested: number;
  }> {
    try {
      const params = `tokens_requested=${tokensRequested}`;
      const response = await api.get(`/admin/quotas/check/${departmentId}/${llmConfigId}?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async updateQuotaUsage(
    departmentId: string, 
    llmConfigId: string, 
    tokensUsed: number
  ): Promise<{
    updated: boolean;
    quota?: Quota;
    tokens_used: number;
    message?: string;
  }> {
    try {
      const params = `tokens_used=${tokensUsed}`;
      const response = await api.post(`/admin/quotas/usage/${departmentId}/${llmConfigId}?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getQuotaUsageStats(filters: {
    days?: number;
    department_id?: string;
    llm_config_id?: string;
  } = {}): Promise<{
    period_days: number;
    total_quotas: number;
    total_usage_tokens: number;
    total_limit_tokens: number;
    average_usage_percentage: number;
    quotas_exceeded: number;
    quotas_at_warning: number;
    department_filter?: string;
    llm_config_filter?: string;
  }> {
    try {
      const params = new URLSearchParams();
      
      if (filters.days !== undefined) params.append('days', filters.days.toString());
      if (filters.department_id) params.append('department_id', filters.department_id);
      if (filters.llm_config_id) params.append('llm_config_id', filters.llm_config_id);
      
      const response = await api.get(`/admin/quotas/stats/usage?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async triggerQuotaAutoReset(): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post('/admin/quotas/maintenance/auto-reset');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  // Usage Monitoring (AID-US-007 Phase 3)
  async getUsageMonitoringDashboard(filters: {
    timeRange?: string;
    departmentId?: string;
    userId?: string;
    modelId?: string;
  } = {}): Promise<import('../types/admin').UsageMonitoringDashboard> {
    try {
      const params = new URLSearchParams();
      
      if (filters.timeRange) params.append('time_range', filters.timeRange);
      if (filters.departmentId) params.append('department_id', filters.departmentId);
      if (filters.userId) params.append('user_id', filters.userId);
      if (filters.modelId) params.append('model_id', filters.modelId);
      
      const response = await api.get(`/admin/usage-monitoring/dashboard?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUsageEntries(filters: import('../types/admin').UsageMonitoringFilters = {}): Promise<import('../types/admin').UsageMonitoringResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.department_id) params.append('department_id', filters.department_id);
      if (filters.user_id) params.append('user_id', filters.user_id);
      if (filters.llm_config_id) params.append('llm_config_id', filters.llm_config_id);
      if (filters.min_tokens !== undefined) params.append('min_tokens', filters.min_tokens.toString());
      if (filters.max_tokens !== undefined) params.append('max_tokens', filters.max_tokens.toString());
      if (filters.time_grouping) params.append('time_grouping', filters.time_grouping);
      if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
      if (filters.offset !== undefined) params.append('offset', filters.offset.toString());
      
      const response = await api.get(`/admin/usage-monitoring/entries?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUsageStats(timeRange: string = '24h'): Promise<import('../types/admin').UsageMonitoringStats> {
    try {
      const response = await api.get(`/admin/usage-monitoring/stats?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getDepartmentUsageStats(timeRange: string = '24h'): Promise<import('../types/admin').DepartmentUsageStats[]> {
    try {
      const response = await api.get(`/admin/usage-monitoring/departments?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUserUsageStats(timeRange: string = '24h', limit: number = 20): Promise<import('../types/admin').UserUsageStats[]> {
    try {
      const response = await api.get(`/admin/usage-monitoring/users?time_range=${timeRange}&limit=${limit}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getModelUsageStats(timeRange: string = '24h'): Promise<import('../types/admin').ModelUsageStats[]> {
    try {
      const response = await api.get(`/admin/usage-monitoring/models?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUsageAlerts(limit: number = 50): Promise<import('../types/admin').UsageAlertsResponse> {
    try {
      const response = await api.get(`/admin/usage-monitoring/alerts?limit=${limit}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async markUsageAlertAsRead(alertId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.post(`/admin/usage-monitoring/alerts/${alertId}/read`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async dismissUsageAlert(alertId: string): Promise<ApiResponse> {
    try {
      const response: AxiosResponse<ApiResponse> = await api.delete(`/admin/usage-monitoring/alerts/${alertId}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getRealTimeMetrics(): Promise<import('../types/admin').RealTimeUsageMetrics> {
    try {
      const response = await api.get('/admin/usage-monitoring/real-time');
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUsageTrends(timeRange: string = '7d'): Promise<import('../types/admin').UsageTrends> {
    try {
      const response = await api.get(`/admin/usage-monitoring/trends?time_range=${timeRange}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async exportUsageData(exportRequest: import('../types/admin').UsageExportRequest): Promise<import('../types/admin').UsageExportResponse> {
    try {
      const response = await api.post('/admin/usage-monitoring/export', exportRequest);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }

  async getUsageTimeseriesData(filters: {
    start_date?: string;
    end_date?: string;
    time_grouping?: 'hour' | 'day' | 'week' | 'month';
    department_id?: string;
    llm_config_id?: string;
  } = {}): Promise<import('../types/admin').UsageTimeseriesData[]> {
    try {
      const params = new URLSearchParams();
      
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      if (filters.time_grouping) params.append('time_grouping', filters.time_grouping);
      if (filters.department_id) params.append('department_id', filters.department_id);
      if (filters.llm_config_id) params.append('llm_config_id', filters.llm_config_id);
      
      const response = await api.get(`/admin/usage-monitoring/timeseries?${params}`);
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      throw new Error(extractErrorMessage(axiosError));
    }
  }
}

// Export singleton instance
export const adminService = new AdminService();
export default adminService;
