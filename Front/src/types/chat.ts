/**
 * TypeScript types for chat functionality
 * Enhanced with quota enforcement types for AID-US-007
 */

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatSendRequest {
  message: string;
  model_id?: string;
  conversation_id?: string;
}

export interface ChatSendResponse {
  response: string;
  model_used: string;
  model_id: string;
  provider: string;
  tokens_prompt: number;
  tokens_completion: number;
  tokens_total: number;
  cost_estimated: number;
  conversation_id?: string;
  usage_log_id: string;
}

export interface ModelInfo {
  id: string;
  model_name: string;
  provider: string;
  enabled: boolean;
  description?: string;
  capabilities?: Record<string, any>;
}

export interface AvailableModelsResponse {
  models: ModelInfo[];
  default_model?: ModelInfo;
  total_count: number;
}

export interface UsageQuotaInfo {
  department_name: string;
  monthly_limit: number;
  current_usage: number;
  usage_percentage: number;
  quota_exceeded: boolean;
  remaining_tokens: number;
}

export interface ChatStatsResponse {
  total_conversations: number;
  total_messages: number;
  total_tokens_used: number;
  total_cost: number;
  most_used_model?: string;
  avg_tokens_per_message: number;
}

export interface ChatHealthResponse {
  status: string;
  available_models: number;
  enabled_models: number;
  default_model?: string;
  quota_status: string;
  timestamp: string;
}

export interface ChatErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
  suggestions?: string[];
  quota_info?: Record<string, any>; // Enhanced for quota errors
  error_code?: string;
  timestamp?: string;
}

// Frontend-specific types
export interface ChatConversation {
  id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
  model_used?: string;
}

export interface ChatState {
  currentConversation: ChatConversation | null;
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  availableModels: ModelInfo[];
  defaultModel: ModelInfo | null;
  quotaInfo: UsageQuotaInfo | null;
  stats: ChatStatsResponse | null;
}

export interface SendMessageOptions {
  message: string;
  modelId?: string;
  conversationId?: string;
}

export interface ChatServiceResponse<T> {
  data?: T;
  error?: ChatErrorResponse;
  success: boolean;
}

// Enhanced types for AID-US-007 Quota Enforcement
export interface QuotaStatusResponse {
  quota_id: string;
  department_name: string;
  llm_model_name: string;
  monthly_limit: number;
  current_usage: number;
  usage_percentage: number;
  is_exceeded: boolean;
  is_warning: boolean;
  remaining_tokens: number;
  last_updated: string;
}

export interface QuotaExceededError {
  error: 'quota_exceeded';
  message: string;
  quota_info: Record<string, any>;
  suggested_actions: string[];
  retry_after?: string;
}

export interface QuotaWarningResponse {
  warning: 'quota_warning';
  message: string;
  quota_info: Record<string, any>;
  usage_percentage: number;
  remaining_tokens: number;
}

export interface EnhancedChatErrorResponse {
  error: string;
  message: string;
  error_code?: string;
  details?: Record<string, any>;
  quota_info?: Record<string, any>;
  suggestions?: string[];
  retry_after?: string;
  timestamp: string;
}

// Enhanced chat state for quota monitoring
export interface EnhancedChatState extends ChatState {
  quotaStatus: QuotaStatusResponse | null;
  quotaWarnings: QuotaWarningResponse[];
  lastQuotaCheck: string | null;
  readinessStatus: {
    ready: boolean;
    health: any;
    quota: any;
    issues: string[];
  } | null;
}

// Quota monitoring options
export interface QuotaMonitoringOptions {
  checkInterval: number; // milliseconds
  warningThreshold: number; // percentage (0-100)
  autoRefresh: boolean;
}

// Chat UI state for quota display
export interface ChatUIState {
  showQuotaStatus: boolean;
  showQuotaWarnings: boolean;
  quotaIndicatorColor: 'green' | 'yellow' | 'red' | 'gray';
  quotaMessage: string;
  canSendMessage: boolean;
}

// Enhanced quota status for real-time monitoring (AID-US-007 Phase 2)
export interface QuotaStatus {
  current_usage: number;
  monthly_limit: number;
  usage_percentage: number;
  is_exceeded: boolean;
  is_warning: boolean;
  remaining_tokens: number;
  department_name: string;
  last_updated: string;
  next_reset_date?: string;
  warning_threshold: number;
  enforcement_mode: 'soft' | 'hard';
}

// Quota error types for enhanced error handling (AID-US-007 Phase 2)
export interface QuotaErrorInfo {
  error_type: 'quota_exceeded' | 'quota_warning' | 'quota_unavailable';
  message: string;
  quota_info: QuotaStatus;
  suggested_actions: string[];
  retry_after?: string;
  contact_admin?: boolean;
}

// Enhanced error state for chat interface (AID-US-007 Phase 2)
export interface ChatErrorState {
  hasError: boolean;
  errorType: 'quota' | 'network' | 'llm' | 'general';
  message: string;
  quotaInfo?: QuotaErrorInfo;
  suggestions: string[];
  isRetryable: boolean;
  showContactAdmin: boolean;
}

// Props for QuotaStatusIndicator component (AID-US-007 Phase 2)
export interface QuotaStatusIndicatorProps {
  quotaInfo: UsageQuotaInfo | null;
  isLoading?: boolean;
  showDetails?: boolean;
  onRefresh?: () => void;
  onContactAdmin?: () => void;
}

// Props for enhanced ModelIndicator with quota status (AID-US-007 Phase 2)
export interface EnhancedModelIndicatorProps {
  currentModel: ModelInfo | null;
  quotaInfo: UsageQuotaInfo | null;
  isLoading?: boolean;
  showQuotaDetails?: boolean;
  onQuotaRefresh?: () => void;
}
