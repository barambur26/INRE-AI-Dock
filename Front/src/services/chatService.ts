/**
 * Chat service for API communication
 * Enhanced with comprehensive quota enforcement for AID-US-007
 */

import {
  ChatSendRequest,
  ChatSendResponse,
  AvailableModelsResponse,
  UsageQuotaInfo,
  ChatStatsResponse,
  ChatHealthResponse,
  ChatServiceResponse,
  SendMessageOptions,
  QuotaStatusResponse
} from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ChatService {
  private baseUrl = `${API_BASE_URL}/api/v1/chat`;

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ChatServiceResponse<T>> {
    try {
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
      
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          error: 'network_error',
          message: `HTTP ${response.status}: ${response.statusText}`,
        }));
        
        return {
          success: false,
          error: errorData,
        };
      }

      const data = await response.json();
      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('Chat service request failed:', error);
      return {
        success: false,
        error: {
          error: 'network_error',
          message: error instanceof Error ? error.message : 'Network request failed',
          suggestions: [
            'Check your internet connection',
            'Verify the backend service is running',
            'Try again in a moment'
          ]
        },
      };
    }
  }

  /**
   * Send a chat message to the LLM
   */
  async sendMessage(options: SendMessageOptions): Promise<ChatServiceResponse<ChatSendResponse>> {
    const request: ChatSendRequest = {
      message: options.message,
      model_id: options.modelId,
      conversation_id: options.conversationId,
    };

    return this.makeRequest<ChatSendResponse>('/send', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get available LLM models
   */
  async getAvailableModels(): Promise<ChatServiceResponse<AvailableModelsResponse>> {
    return this.makeRequest<AvailableModelsResponse>('/models');
  }

  /**
   * Get usage quota information
   */
  async getUsageQuota(): Promise<ChatServiceResponse<UsageQuotaInfo>> {
    return this.makeRequest<UsageQuotaInfo>('/quota');
  }

  /**
   * Get detailed quota status for real-time monitoring (AID-US-007)
   */
  async getQuotaStatus(modelId?: string): Promise<ChatServiceResponse<QuotaStatusResponse>> {
    const endpoint = modelId ? `/quota/status?model_id=${modelId}` : '/quota/status';
    return this.makeRequest<QuotaStatusResponse>(endpoint);
  }

  /**
   * Get chat statistics
   */
  async getChatStats(): Promise<ChatServiceResponse<ChatStatsResponse>> {
    return this.makeRequest<ChatStatsResponse>('/stats');
  }

  /**
   * Get chat service health status
   */
  async getHealthStatus(): Promise<ChatServiceResponse<ChatHealthResponse>> {
    return this.makeRequest<ChatHealthResponse>('/health');
  }

  /**
   * Test chat service connectivity
   */
  async testConnection(): Promise<ChatServiceResponse<any>> {
    return this.makeRequest<any>('/test');
  }

  /**
   * Check if chat service is ready (Enhanced for AID-US-007)
   */
  async isReady(): Promise<boolean> {
    try {
      const healthResponse = await this.getHealthStatus();
      const quotaResponse = await this.getUsageQuota();
      
      return (
        healthResponse.success &&
        healthResponse.data?.status === 'healthy' &&
        quotaResponse.success &&
        !quotaResponse.data?.quota_exceeded
      );
    } catch (error) {
      console.error('Error checking chat service readiness:', error);
      return false;
    }
  }

  /**
   * Enhanced readiness check with detailed status (AID-US-007)
   */
  async getDetailedReadinessStatus(): Promise<{
    ready: boolean;
    health: any;
    quota: any;
    issues: string[];
  }> {
    const issues: string[] = [];
    
    try {
      const [healthResponse, quotaResponse] = await Promise.all([
        this.getHealthStatus(),
        this.getUsageQuota()
      ]);
      
      let ready = true;
      
      // Check health
      if (!healthResponse.success || healthResponse.data?.status !== 'healthy') {
        ready = false;
        issues.push('Chat service is not healthy');
      }
      
      // Check quota
      if (!quotaResponse.success) {
        ready = false;
        issues.push('Unable to retrieve quota information');
      } else if (quotaResponse.data?.quota_exceeded) {
        ready = false;
        issues.push('Monthly quota has been exceeded');
      } else if (quotaResponse.data?.usage_percentage >= 95) {
        issues.push('Quota usage is very high (>95%)');
      }
      
      return {
        ready,
        health: healthResponse.data,
        quota: quotaResponse.data,
        issues
      };
    } catch (error) {
      console.error('Error checking detailed readiness status:', error);
      return {
        ready: false,
        health: null,
        quota: null,
        issues: ['Failed to check service status']
      };
    }
  }

  /**
   * Format error message for user display (Enhanced for AID-US-007)
   */
  formatErrorMessage(error: any): string {
    // Enhanced quota exceeded error with detailed information
    if (error?.error === 'quota_exceeded') {
      const quotaInfo = error?.quota_info;
      if (quotaInfo) {
        const current = quotaInfo.current_usage?.toLocaleString() || 'unknown';
        const limit = quotaInfo.limit?.toLocaleString() || 'unknown';
        const remaining = quotaInfo.remaining_tokens?.toLocaleString() || '0';
        
        if (quotaInfo.remaining_tokens > 0) {
          return `You have ${remaining} tokens remaining this month. This request would exceed your department's quota (${current}/${limit} tokens used).`;
        } else {
          return `Your department has exceeded its monthly quota of ${limit} tokens (currently used: ${current}). The quota resets next month.`;
        }
      }
      return 'Your department has exceeded its monthly usage quota. Please contact your administrator.';
    }
    
    // Quota warning messages
    if (error?.warning === 'quota_warning') {
      const quotaInfo = error?.quota_info;
      const percentage = error?.usage_percentage || quotaInfo?.usage_percentage_after;
      if (percentage) {
        return `Warning: This request will use ${percentage.toFixed(1)}% of your monthly quota.`;
      }
      return 'Warning: You are approaching your monthly quota limit.';
    }
    
    if (error?.error === 'no_models_available') {
      return 'No LLM models are currently available. Please contact your administrator to configure models.';
    }
    
    if (error?.error === 'llm_provider_error') {
      return 'The AI service is temporarily unavailable. Please try again in a few moments.';
    }
    
    if (error?.error === 'network_error') {
      return 'Unable to connect to the chat service. Please check your connection and try again.';
    }
    
    if (error?.error === 'chat_service_error') {
      return 'There was an issue with the chat service. Please try again.';
    }
    
    // Use the server-provided message if available
    return error?.message || 'An unexpected error occurred. Please try again.';
  }

  /**
   * Get error suggestions for user (Enhanced for AID-US-007)
   */
  getErrorSuggestions(error: any): string[] {
    // Use server-provided suggestions first
    if (error?.suggested_actions && Array.isArray(error.suggested_actions)) {
      return error.suggested_actions;
    }
    
    if (error?.suggestions && Array.isArray(error.suggestions)) {
      return error.suggestions;
    }
    
    // Enhanced suggestions based on error type
    if (error?.error === 'quota_exceeded') {
      const suggestions = ['Contact your administrator to increase quota limits'];
      
      const quotaInfo = error?.quota_info;
      if (quotaInfo?.remaining_tokens > 0) {
        suggestions.unshift('Try a shorter message to stay within your remaining quota');
      }
      
      suggestions.push('Wait until next month for automatic quota reset');
      return suggestions;
    }
    
    if (error?.error === 'no_models_available') {
      return [
        'Contact your administrator to configure LLM models',
        'Check if any models are enabled in admin settings',
        'Verify your department has access to LLM models'
      ];
    }
    
    if (error?.error === 'llm_provider_error') {
      return [
        'Try again in a few moments',
        'Try using a different model if available',
        'Contact support if the issue persists'
      ];
    }
    
    // Default suggestions
    return [
      'Try refreshing the page',
      'Check your internet connection',
      'Contact support if the issue persists'
    ];
  }

  /**
   * Check if error is quota-related (AID-US-007)
   */
  isQuotaError(error: any): boolean {
    return error?.error === 'quota_exceeded' || error?.warning === 'quota_warning';
  }

  /**
   * Get quota information from error (AID-US-007)
   */
  getQuotaInfoFromError(error: any): any {
    return error?.quota_info || null;
  }

  /**
   * Check if quota warning should be displayed (AID-US-007)
   */
  isQuotaWarning(error: any): boolean {
    return error?.warning === 'quota_warning' || 
           (error?.quota_info?.usage_percentage_after >= 80 && error?.error !== 'quota_exceeded');
  }

  /**
   * Get user-friendly quota status message (AID-US-007)
   */
  getQuotaStatusMessage(quotaData: any): string {
    if (!quotaData) return 'Quota information unavailable';
    
    const {
      current_usage = 0,
      monthly_limit = 0,
      usage_percentage = 0,
      is_exceeded = false,
      is_warning = false,
      remaining_tokens = 0
    } = quotaData;
    
    if (monthly_limit === 0) {
      return 'No quota limits applied';
    }
    
    if (is_exceeded) {
      return `Quota exceeded: ${current_usage.toLocaleString()}/${monthly_limit.toLocaleString()} tokens (${usage_percentage.toFixed(1)}%)`;
    }
    
    if (is_warning) {
      return `Quota warning: ${usage_percentage.toFixed(1)}% used (${remaining_tokens.toLocaleString()} tokens remaining)`;
    }
    
    return `Quota status: ${usage_percentage.toFixed(1)}% used (${remaining_tokens.toLocaleString()} tokens remaining)`;
  }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService;
