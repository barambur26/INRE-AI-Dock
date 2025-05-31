/**
 * TypeScript interfaces for admin operations
 */

// User Types
export interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  role_id?: string;
  department_id?: string;
  created_at: string;
  updated_at: string;
  role_name?: string;
  department_name?: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  is_active?: boolean;
  is_superuser?: boolean;
  role_id?: string;
  department_id?: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  password?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  role_id?: string;
  department_id?: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Department Types
export interface Department {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_count: number;
  active_user_count: number;
}

export interface DepartmentCreate {
  name: string;
  description?: string;
}

export interface DepartmentUpdate {
  name?: string;
  description?: string;
}

export interface DepartmentListResponse {
  departments: Department[];
  total: number;
}

// Role Types
export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  created_at: string;
  updated_at: string;
  user_count: number;
  is_admin_role: boolean;
}

export interface RoleCreate {
  name: string;
  description?: string;
  permissions: string[];
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permissions?: string[];
}

export interface RoleListResponse {
  roles: Role[];
  total: number;
}

// LLM Configuration Types
export interface LLMConfiguration {
  id: string;
  model_name: string;
  provider: string;
  display_name?: string;
  base_url?: string;
  enabled: boolean;
  api_key_encrypted?: string;
  config_json: Record<string, any>;
  created_at: string;
  updated_at: string;
  quota_count: number;
  usage_count: number;
}

export interface LLMConfigCreate {
  model_name: string;
  provider: string;
  display_name?: string;
  base_url?: string;
  enabled?: boolean;
  api_key_env_var?: string;
  config_json?: Record<string, any>;
}

export interface LLMConfigUpdate {
  model_name?: string;
  provider?: string;
  display_name?: string;
  base_url?: string;
  enabled?: boolean;
  api_key_env_var?: string;
  config_json?: Record<string, any>;
}

export interface LLMConfigListResponse {
  configurations: LLMConfiguration[];
  total: number;
  enabled_count: number;
  disabled_count: number;
  providers: string[];
}

export interface LLMConfigurationJSON {
  model_name: string;
  provider: string;
  display_name?: string;
  api_key_env_var?: string;
  base_url?: string;
  enabled?: boolean;
  config: Record<string, any>;
}

export interface LLMConfigurationJSONInput {
  configurations: LLMConfigurationJSON[];
}

export interface ValidationIssue {
  level: string;
  message: string;
  field?: string;
  suggestion?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  issues: ValidationIssue[];
  suggestions?: string[];
}

export interface LLMConfigValidationResponse {
  configurations: any[];
  validation_results: ValidationResult[];
  overall_valid: boolean;
  summary: {
    total_configurations: number;
    valid_configurations: number;
    configurations_with_warnings: number;
    configurations_with_errors: number;
  };
}

export interface BulkLLMConfigUpdate {
  config_ids: string[];
  updates: LLMConfigUpdate;
}

export interface BulkLLMConfigResponse {
  success_count: number;
  error_count: number;
  errors: Array<{
    config_id: string;
    error: string;
  }>;
  updated_configurations?: LLMConfiguration[];
}

export interface LLMConfigStats {
  total_configurations: number;
  enabled_configurations: number;
  disabled_configurations: number;
  configurations_by_provider: Record<string, number>;
  total_usage_logs: number;
  total_quotas: number;
  most_used_models: Array<{
    model_name: string;
    provider: string;
    usage_count: number;
  }>;
  recent_configurations: number;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  supported_models: string[];
  default_config: Record<string, any>;
  required_env_vars: string[];
  documentation_url?: string;
}

export interface ProvidersResponse {
  providers: ProviderInfo[];
  total_providers: number;
  total_models: number;
}

export interface LLMConfigUsageSummary {
  configuration: LLMConfiguration;
  total_tokens_used: number;
  total_requests: number;
  recent_tokens_used: number;
  department_quotas: number;
  active_quotas: number;
}

// Permission Types
export interface PermissionInfo {
  name: string;
  description: string;
  category: string;
}

export interface AvailablePermissionsResponse {
  permissions: PermissionInfo[];
  categories: string[];
}

// Admin Statistics
export interface AdminStats {
  total_users: number;
  active_users: number;
  total_departments: number;
  total_roles: number;
  users_by_role: Record<string, number>;
  users_by_department: Record<string, number>;
  recent_users_count: number;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status: 'success' | 'error';
}

// Form Data Types
export interface UserFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  is_active: boolean;
  is_superuser: boolean;
  role_id: string;
  department_id: string;
}

export interface DepartmentFormData {
  name: string;
  description: string;
}

export interface RoleFormData {
  name: string;
  description: string;
  permissions: string[];
}

// Filter Types
export interface UserFilters {
  search?: string;
  role_id?: string;
  department_id?: string;
  is_active?: boolean;
  page?: number;
  limit?: number;
}

// Action Types
export type AdminAction = 
  | 'create'
  | 'edit'
  | 'delete'
  | 'activate'
  | 'deactivate'
  | 'reset_password'
  | 'assign_role'
  | 'assign_department';

// Modal Types
export interface ModalState {
  isOpen: boolean;
  mode: 'create' | 'edit' | 'view';
  data?: any;
}

// Table Types
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: any) => React.ReactNode;
}

export interface TableAction {
  label: string;
  action: string;
  icon?: React.ReactNode;
  variant?: 'default' | 'destructive' | 'outline';
  condition?: (item: any) => boolean;
}

// Bulk Operations
export interface BulkOperation {
  action: string;
  label: string;
  icon?: React.ReactNode;
  confirmMessage?: string;
}

export interface BulkUserUpdate {
  user_ids: string[];
  updates: UserUpdate;
}

export interface BulkResponse {
  success_count: number;
  error_count: number;
  errors: Array<{
    user_id: string;
    error: string;
  }>;
}

// Navigation Types
export interface AdminNavItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  count?: number;
  href?: string;
}

// Loading States
export interface LoadingState {
  users: boolean;
  departments: boolean;
  roles: boolean;
  stats: boolean;
  permissions: boolean;
}

// Error Types
export interface ErrorState {
  users?: string;
  departments?: string;
  roles?: string;
  stats?: string;
  general?: string;
}

// Success Types
export interface SuccessState {
  users?: string;
  departments?: string;
  roles?: string;
  general?: string;
}

// Admin Context Type
export interface AdminContextType {
  // Data
  users: User[];
  departments: Department[];
  roles: Role[];
  quotas: Quota[];
  stats: AdminStats | null;
  permissions: PermissionInfo[];
  
  // Loading states
  loading: LoadingState & {
    quotas: boolean;
  };
  
  // Error states
  errors: ErrorState & {
    quotas?: string;
  };
  
  // Success states
  success: SuccessState & {
    quotas?: string;
  };
  
  // Actions
  refreshUsers: () => Promise<void>;
  refreshDepartments: () => Promise<void>;
  refreshRoles: () => Promise<void>;
  refreshQuotas: () => Promise<void>;
  refreshStats: () => Promise<void>;
  refreshPermissions: () => Promise<void>;
  
  // CRUD operations
  createUser: (data: UserCreate) => Promise<User>;
  updateUser: (id: string, data: UserUpdate) => Promise<User>;
  deleteUser: (id: string) => Promise<void>;
  
  createDepartment: (data: DepartmentCreate) => Promise<Department>;
  updateDepartment: (id: string, data: DepartmentUpdate) => Promise<Department>;
  deleteDepartment: (id: string) => Promise<void>;
  
  createRole: (data: RoleCreate) => Promise<Role>;
  updateRole: (id: string, data: RoleUpdate) => Promise<Role>;
  deleteRole: (id: string) => Promise<void>;
  
  createQuota: (data: QuotaCreate) => Promise<Quota>;
  updateQuota: (id: string, data: QuotaUpdate) => Promise<Quota>;
  deleteQuota: (id: string) => Promise<void>;
  
  // Clear messages
  clearErrors: () => void;
  clearSuccess: () => void;
}

// Component Props Types
export interface UserTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (userId: string) => void;
  onActivate: (userId: string) => void;
  onDeactivate: (userId: string) => void;
  loading?: boolean;
}

export interface DepartmentTableProps {
  departments: Department[];
  onEdit: (department: Department) => void;
  onDelete: (departmentId: string) => void;
  loading?: boolean;
}

export interface RoleTableProps {
  roles: Role[];
  onEdit: (role: Role) => void;
  onDelete: (roleId: string) => void;
  loading?: boolean;
}

export interface UserFormProps {
  mode: 'create' | 'edit';
  initialData?: User;
  onSubmit: (data: UserCreate | UserUpdate) => void;
  onCancel: () => void;
  loading?: boolean;
  departments: Department[];
  roles: Role[];
}

export interface DepartmentFormProps {
  mode: 'create' | 'edit';
  initialData?: Department;
  onSubmit: (data: DepartmentCreate | DepartmentUpdate) => void;
  onCancel: () => void;
  loading?: boolean;
}

export interface RoleFormProps {
  mode: 'create' | 'edit';
  initialData?: Role;
  onSubmit: (data: RoleCreate | RoleUpdate) => void;
  onCancel: () => void;
  loading?: boolean;
  availablePermissions: PermissionInfo[];
}

// Quota Types
export type QuotaEnforcement = 'soft_warning' | 'hard_block';
export type QuotaTemplate = 'small_department' | 'medium_department' | 'large_department' | 'unlimited';

export interface Quota {
  id: string;
  department_id: string;
  llm_config_id: string;
  monthly_limit_tokens: number;
  daily_limit_tokens: number;
  monthly_limit_requests: number;
  daily_limit_requests: number;
  current_usage_tokens: number;
  current_daily_usage_tokens: number;
  current_usage_requests: number;
  current_daily_usage_requests: number;
  enforcement_mode: QuotaEnforcement;
  warning_threshold_percent: number;
  last_reset: string;
  created_at: string;
  updated_at: string;
  // Calculated fields
  monthly_usage_percentage: number;
  daily_usage_percentage: number;
  is_quota_exceeded: boolean;
  is_warning_threshold_reached: boolean;
  // Related data
  department_name?: string;
  llm_model_name?: string;
  llm_provider?: string;
}

export interface QuotaCreate {
  department_id: string;
  llm_config_id: string;
  monthly_limit_tokens?: number;
  daily_limit_tokens?: number;
  monthly_limit_requests?: number;
  daily_limit_requests?: number;
  enforcement_mode?: QuotaEnforcement;
  warning_threshold_percent?: number;
}

export interface QuotaUpdate {
  monthly_limit_tokens?: number;
  daily_limit_tokens?: number;
  monthly_limit_requests?: number;
  daily_limit_requests?: number;
  enforcement_mode?: QuotaEnforcement;
  warning_threshold_percent?: number;
}

export interface QuotaListResponse {
  quotas: Quota[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface QuotaFilters {
  department_id?: string;
  llm_config_id?: string;
  enforcement_mode?: QuotaEnforcement;
  exceeded_only?: boolean;
  warning_only?: boolean;
}

export interface QuotaTemplateSettings {
  name: string;
  description: string;
  monthly_limit_tokens: number;
  daily_limit_tokens: number;
  monthly_limit_requests: number;
  daily_limit_requests: number;
  enforcement_mode: QuotaEnforcement;
  warning_threshold_percent: number;
}

export interface QuotaTemplatesResponse {
  templates: QuotaTemplateSettings[];
}

export interface BulkQuotaCreate {
  department_ids: string[];
  llm_config_ids: string[];
  quota_template?: QuotaTemplate;
  quota_settings?: QuotaCreate;
}

export interface BulkQuotaUpdate {
  quota_ids: string[];
  updates: QuotaUpdate;
}

export interface BulkQuotaResponse {
  success_count: number;
  error_count: number;
  created_quotas?: string[];
  errors: Array<{
    quota_id?: string;
    department_id?: string;
    llm_config_id?: string;
    error: string;
  }>;
}

export interface QuotaOverviewStats {
  total_quotas: number;
  quotas_exceeded: number;
  quotas_at_warning: number;
  departments_with_quotas: number;
  llm_configs_with_quotas: number;
  average_usage_percentage: number;
  top_usage_departments: Array<{
    department_name: string;
    usage_percentage: number;
    tokens_used: number;
    tokens_limit: number;
  }>;
  quota_enforcement_breakdown: Record<string, number>;
}

export interface DepartmentQuotaSummary {
  department_id: string;
  department_name: string;
  total_quotas: number;
  exceeded_quotas: number;
  warning_quotas: number;
  total_monthly_tokens_used: number;
  total_monthly_tokens_limit: number;
  overall_usage_percentage: number;
}

export interface QuotaAlert {
  quota_id: string;
  department_name: string;
  llm_model_name: string;
  alert_type: 'warning' | 'exceeded' | 'reset';
  message: string;
  usage_percentage: number;
  timestamp: string;
}

export interface QuotaAlertsResponse {
  alerts: QuotaAlert[];
  total_alerts: number;
  unread_alerts: number;
}

export interface QuotaResetRequest {
  quota_ids: string[];
  reset_type?: string;
}

export interface QuotaResetResponse {
  success_count: number;
  error_count: number;
  reset_quotas: string[];
  errors: Array<{
    quota_id: string;
    error: string;
  }>;
}

export interface QuotaUsageStats {
  quota_id: string;
  department_name: string;
  llm_model_name: string;
  monthly_tokens_used: number;
  monthly_tokens_limit: number;
  daily_tokens_used: number;
  daily_tokens_limit: number;
  monthly_requests_used: number;
  monthly_requests_limit: number;
  daily_requests_used: number;
  daily_requests_limit: number;
  usage_percentage: number;
  enforcement_mode: QuotaEnforcement;
  is_exceeded: boolean;
  days_until_reset: number;
}

// Quota Form Data Types
export interface QuotaFormData {
  department_id: string;
  llm_config_id: string;
  monthly_limit_tokens: number;
  daily_limit_tokens: number;
  monthly_limit_requests: number;
  daily_limit_requests: number;
  enforcement_mode: QuotaEnforcement;
  warning_threshold_percent: number;
}

// Quota Component Props
export interface QuotaManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

export interface QuotaTableProps {
  quotas: Quota[];
  onEdit: (quota: Quota) => void;
  onDelete: (quotaId: string) => void;
  loading?: boolean;
}

export interface QuotaFormProps {
  mode: 'create' | 'edit';
  initialData?: Quota;
  onSubmit: (data: QuotaCreate | QuotaUpdate) => void;
  onCancel: () => void;
  loading?: boolean;
  departments: Department[];
  llmConfigurations: LLMConfiguration[];
  templates: QuotaTemplateSettings[];
}

// Usage Monitoring Types (AID-US-007 Phase 3)
export interface UsageEntry {
  id: string;
  user_id: string;
  department_id: string;
  llm_config_id: string;
  timestamp: string;
  tokens_used: number;
  cost_estimated: number;
  request_details?: Record<string, any>;
  // Related data
  username?: string;
  department_name?: string;
  llm_model_name?: string;
  llm_provider?: string;
}

export interface UsageMonitoringStats {
  total_requests: number;
  total_tokens_used: number;
  total_cost_estimated: number;
  unique_users: number;
  active_departments: number;
  active_models: number;
  avg_tokens_per_request: number;
  avg_cost_per_request: number;
  peak_usage_hour: number;
  requests_last_24h: number;
  tokens_last_24h: number;
}

export interface DepartmentUsageStats {
  department_id: string;
  department_name: string;
  total_requests: number;
  total_tokens_used: number;
  total_cost_estimated: number;
  unique_users: number;
  quota_usage_percentage: number;
  quota_limit_tokens: number;
  is_quota_exceeded: boolean;
  is_warning_threshold_reached: boolean;
  last_activity: string;
  top_users: Array<{
    username: string;
    tokens_used: number;
    requests: number;
  }>;
}

export interface UserUsageStats {
  user_id: string;
  username: string;
  department_name: string;
  total_requests: number;
  total_tokens_used: number;
  total_cost_estimated: number;
  avg_tokens_per_request: number;
  last_activity: string;
  most_used_model: string;
  requests_by_model: Record<string, number>;
}

export interface ModelUsageStats {
  llm_config_id: string;
  model_name: string;
  provider: string;
  total_requests: number;
  total_tokens_used: number;
  total_cost_estimated: number;
  unique_users: number;
  avg_tokens_per_request: number;
  last_used: string;
  requests_by_department: Record<string, number>;
  usage_trend: Array<{
    date: string;
    requests: number;
    tokens: number;
  }>;
}

export interface UsageTimeseriesData {
  timestamp: string;
  requests: number;
  tokens: number;
  cost: number;
  unique_users: number;
}

export interface UsageMonitoringFilters {
  start_date?: string;
  end_date?: string;
  department_id?: string;
  user_id?: string;
  llm_config_id?: string;
  min_tokens?: number;
  max_tokens?: number;
  time_grouping?: 'hour' | 'day' | 'week' | 'month';
  limit?: number;
  offset?: number;
}

export interface UsageMonitoringResponse {
  usage_entries: UsageEntry[];
  total_count: number;
  filtered_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: {
    total_requests: number;
    total_tokens: number;
    total_cost: number;
    unique_users: number;
    date_range: {
      start: string;
      end: string;
    };
  };
}

export interface UsageAlert {
  id: string;
  alert_type: 'quota_warning' | 'quota_exceeded' | 'unusual_usage' | 'high_cost' | 'model_error';
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  is_read: boolean;
  related_department?: string;
  related_user?: string;
  related_model?: string;
  action_required: boolean;
  metadata?: Record<string, any>;
}

export interface UsageAlertsResponse {
  alerts: UsageAlert[];
  total_alerts: number;
  unread_alerts: number;
  alerts_by_severity: Record<string, number>;
}

export interface UsageExportRequest {
  format: 'csv' | 'xlsx' | 'json';
  filters: UsageMonitoringFilters;
  include_user_details?: boolean;
  include_cost_breakdown?: boolean;
  include_quota_status?: boolean;
}

export interface UsageExportResponse {
  export_id: string;
  download_url: string;
  expires_at: string;
  file_size_bytes: number;
  record_count: number;
}

export interface RealTimeUsageMetrics {
  current_active_users: number;
  requests_per_minute: number;
  tokens_per_minute: number;
  avg_response_time_ms: number;
  error_rate_percentage: number;
  quota_alerts_count: number;
  system_health_score: number;
  last_updated: string;
}

export interface UsageThresholds {
  daily_requests_warning: number;
  daily_tokens_warning: number;
  hourly_requests_warning: number;
  cost_per_request_warning: number;
  error_rate_warning: number;
  response_time_warning_ms: number;
}

export interface UsageTrends {
  requests_trend: {
    current_period: number;
    previous_period: number;
    percentage_change: number;
    trend_direction: 'up' | 'down' | 'stable';
  };
  tokens_trend: {
    current_period: number;
    previous_period: number;
    percentage_change: number;
    trend_direction: 'up' | 'down' | 'stable';
  };
  cost_trend: {
    current_period: number;
    previous_period: number;
    percentage_change: number;
    trend_direction: 'up' | 'down' | 'stable';
  };
  users_trend: {
    current_period: number;
    previous_period: number;
    percentage_change: number;
    trend_direction: 'up' | 'down' | 'stable';
  };
}

export interface UsageMonitoringDashboard {
  overview_stats: UsageMonitoringStats;
  real_time_metrics: RealTimeUsageMetrics;
  department_stats: DepartmentUsageStats[];
  top_users: UserUsageStats[];
  model_stats: ModelUsageStats[];
  recent_alerts: UsageAlert[];
  usage_trends: UsageTrends;
  timeseries_data: UsageTimeseriesData[];
  quota_summary: QuotaOverviewStats;
}

// Usage Monitoring Component Props
export interface UsageMonitoringProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

export interface UsageChartProps {
  data: UsageTimeseriesData[];
  metric: 'requests' | 'tokens' | 'cost' | 'users';
  timeRange: string;
  height?: number;
}

export interface UsageTableProps {
  entries: UsageEntry[];
  loading?: boolean;
  onRefresh?: () => void;
  onExport?: () => void;
}

export interface DepartmentUsageCardProps {
  department: DepartmentUsageStats;
  onViewDetails: (departmentId: string) => void;
}

export interface UsageAlertsProps {
  alerts: UsageAlert[];
  onMarkAsRead: (alertId: string) => void;
  onDismiss: (alertId: string) => void;
}

export interface RealTimeMetricsProps {
  metrics: RealTimeUsageMetrics;
  thresholds: UsageThresholds;
  onRefresh: () => void;
}
