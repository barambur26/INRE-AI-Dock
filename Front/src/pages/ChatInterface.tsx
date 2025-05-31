/**
 * ChatInterface page - Main chat interface for LLM interactions
 * Enhanced for AID-US-007 Phase 2: Advanced quota enforcement and error handling
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useLogout } from '../hooks/useAuth';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import MessageList from '../components/chat/MessageList';
import MessageInput from '../components/chat/MessageInput';
import ModelIndicator from '../components/chat/ModelIndicator';
import chatService from '../services/chatService';
import {
  ChatMessage,
  ChatConversation,
  ModelInfo,
  UsageQuotaInfo,
  ChatServiceResponse,
  ChatSendResponse,
  ChatErrorState
} from '../types/chat';
import {
  ArrowLeft,
  AlertCircle,
  RefreshCw,
  Settings,
  BarChart3,
  LogOut,
  XCircle,
  AlertTriangle,
  Mail,
  HelpCircle
} from 'lucide-react';

const ChatInterface: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();
  const { logout, isLoading: isLoggingOut } = useLogout();
  const navigate = useNavigate();

  // Chat state
  const [conversation, setConversation] = useState<ChatConversation>({
    id: crypto.randomUUID(),
    messages: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  });
  
  const [isSending, setIsSending] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  
  // Enhanced error state (AID-US-007 Phase 2)
  const [errorState, setErrorState] = useState<ChatErrorState>({
    hasError: false,
    errorType: 'general',
    message: '',
    suggestions: [],
    isRetryable: false,
    showContactAdmin: false
  });
  
  // Model and quota state
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [currentModel, setCurrentModel] = useState<ModelInfo | null>(null);
  const [quotaInfo, setQuotaInfo] = useState<UsageQuotaInfo | null>(null);
  
  // Service status
  const [isServiceReady, setIsServiceReady] = useState(false);
  const [lastQuotaCheck, setLastQuotaCheck] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Enhanced quota monitoring (check every 30 seconds when active)
  useEffect(() => {
    if (!isServiceReady) return;

    const quotaCheckInterval = setInterval(() => {
      refreshQuotaInfo();
    }, 30000); // 30 seconds

    return () => clearInterval(quotaCheckInterval);
  }, [isServiceReady]);

  const loadInitialData = async () => {
    setIsLoadingData(true);
    clearError();

    try {
      // Load available models
      const modelsResponse = await chatService.getAvailableModels();
      if (modelsResponse.success && modelsResponse.data) {
        setAvailableModels(modelsResponse.data.models);
        setCurrentModel(modelsResponse.data.default_model || modelsResponse.data.models[0] || null);
      }

      // Load quota information
      await refreshQuotaInfo();

      // Check service readiness
      const ready = await chatService.isReady();
      setIsServiceReady(ready);

    } catch (error) {
      console.error('Error loading initial data:', error);
      setErrorState({
        hasError: true,
        errorType: 'network',
        message: 'Failed to load chat data. Please try refreshing the page.',
        suggestions: [
          'Check your internet connection',
          'Refresh the page',
          'Contact support if the issue persists'
        ],
        isRetryable: true,
        showContactAdmin: false
      });
    } finally {
      setIsLoadingData(false);
    }
  };

  const refreshQuotaInfo = async () => {
    try {
      const quotaResponse = await chatService.getUsageQuota();
      if (quotaResponse.success && quotaResponse.data) {
        setQuotaInfo(quotaResponse.data);
        setLastQuotaCheck(new Date().toISOString());
      }
    } catch (error) {
      console.error('Error refreshing quota info:', error);
    }
  };

  // Enhanced error handling (AID-US-007 Phase 2)
  const handleChatError = (error: any) => {
    console.error('Chat error:', error);

    // Check if it's a quota error
    if (chatService.isQuotaError(error)) {
      const quotaInfo = chatService.getQuotaInfoFromError(error);
      
      setErrorState({
        hasError: true,
        errorType: 'quota',
        message: chatService.formatErrorMessage(error),
        quotaInfo: {
          error_type: error.error === 'quota_exceeded' ? 'quota_exceeded' : 'quota_warning',
          message: chatService.formatErrorMessage(error),
          quota_info: quotaInfo || {},
          suggested_actions: chatService.getErrorSuggestions(error),
          contact_admin: error.error === 'quota_exceeded'
        },
        suggestions: chatService.getErrorSuggestions(error),
        isRetryable: error.error !== 'quota_exceeded',
        showContactAdmin: error.error === 'quota_exceeded'
      });
    } else if (error?.error === 'no_models_available') {
      setErrorState({
        hasError: true,
        errorType: 'llm',
        message: 'No LLM models are currently available.',
        suggestions: [
          'Contact your administrator to configure models',
          'Check if any models are enabled in admin settings',
          'Verify your department has access to LLM models'
        ],
        isRetryable: false,
        showContactAdmin: true
      });
    } else if (error?.error === 'llm_provider_error') {
      setErrorState({
        hasError: true,
        errorType: 'llm',
        message: 'The AI service is temporarily unavailable.',
        suggestions: [
          'Try again in a few moments',
          'Try using a different model if available',
          'Contact support if the issue persists'
        ],
        isRetryable: true,
        showContactAdmin: false
      });
    } else {
      setErrorState({
        hasError: true,
        errorType: 'general',
        message: chatService.formatErrorMessage(error),
        suggestions: chatService.getErrorSuggestions(error),
        isRetryable: true,
        showContactAdmin: false
      });
    }
  };

  const clearError = () => {
    setErrorState({
      hasError: false,
      errorType: 'general',
      message: '',
      suggestions: [],
      isRetryable: false,
      showContactAdmin: false
    });
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || isSending || !isServiceReady) {
      return;
    }

    // Clear any previous errors
    clearError();

    setIsSending(true);

    // Add user message to conversation
    const userMessage: ChatMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setConversation(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      updated_at: new Date().toISOString()
    }));

    try {
      // Send message to LLM
      const response = await chatService.sendMessage({
        message: messageText,
        modelId: currentModel?.id,
        conversationId: conversation.id
      });

      if (response.success && response.data) {
        // Add assistant response to conversation
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date().toISOString()
        };

        setConversation(prev => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          updated_at: new Date().toISOString(),
          model_used: response.data.model_used
        }));

        // Refresh quota info after successful message
        await refreshQuotaInfo();
      } else {
        // Handle error response with enhanced error handling
        handleChatError(response.error);
        
        // Remove the user message if the request failed
        setConversation(prev => ({
          ...prev,
          messages: prev.messages.slice(0, -1)
        }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      handleChatError(error);
      
      // Remove the user message if the request failed
      setConversation(prev => ({
        ...prev,
        messages: prev.messages.slice(0, -1)
      }));
    } finally {
      setIsSending(false);
    }
  };

  const handleRefresh = () => {
    clearError();
    loadInitialData();
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleContactAdmin = () => {
    // In a real implementation, this could open a modal, redirect to a contact form,
    // or trigger an email composition
    const subject = encodeURIComponent('AI Dock - Quota Limit Request');
    const body = encodeURIComponent(
      `Hello,\n\nI need assistance with my AI Dock quota limits.\n\n` +
      `Department: ${quotaInfo?.department_name || 'Unknown'}\n` +
      `Current Usage: ${quotaInfo?.current_usage?.toLocaleString() || 'Unknown'} tokens\n` +
      `Monthly Limit: ${quotaInfo?.monthly_limit?.toLocaleString() || 'Unknown'} tokens\n\n` +
      `Please help me with:\n- Increasing quota limits\n- Understanding usage patterns\n- Other: \n\n` +
      `Thank you!`
    );
    
    window.open(`mailto:admin@company.com?subject=${subject}&body=${body}`, '_blank');
  };

  const isAdmin = user?.is_superuser || user?.role_name === 'admin' || user?.role === 'admin';

  // Determine if user can send messages
  const canSendMessage = isServiceReady && 
                        !quotaInfo?.quota_exceeded && 
                        !errorState.hasError && 
                        currentModel?.enabled;

  if (authLoading || isLoadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-sm text-gray-600">Loading chat interface...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                className="p-2"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">AI Chat</h1>
                <p className="text-sm text-gray-500">LLM Conversation Interface</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoadingData}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoadingData ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              
              {isAdmin && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/admin')}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Admin
                </Button>
              )}
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                ) : (
                  <>
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Enhanced Model indicator with quota details */}
      <ModelIndicator
        currentModel={currentModel}
        quotaInfo={quotaInfo}
        isLoading={isLoadingData}
        showQuotaDetails={true}
        onQuotaRefresh={refreshQuotaInfo}
        onContactAdmin={handleContactAdmin}
      />

      {/* Enhanced Error Display (AID-US-007 Phase 2) */}
      {errorState.hasError && (
        <div className={`mx-4 mt-4 rounded-lg border-l-4 p-4 ${
          errorState.errorType === 'quota' 
            ? 'bg-red-50 border-red-400'
            : errorState.errorType === 'network'
            ? 'bg-yellow-50 border-yellow-400' 
            : 'bg-red-50 border-red-400'
        }`}>
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {errorState.errorType === 'quota' ? (
                <XCircle className="h-5 w-5 text-red-400" />
              ) : errorState.errorType === 'network' ? (
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-400" />
              )}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h3 className={`text-sm font-medium ${
                  errorState.errorType === 'quota' 
                    ? 'text-red-800'
                    : errorState.errorType === 'network'
                    ? 'text-yellow-800'
                    : 'text-red-800'
                }`}>
                  {errorState.errorType === 'quota' ? 'Quota Issue' :
                   errorState.errorType === 'network' ? 'Connection Issue' :
                   errorState.errorType === 'llm' ? 'Service Issue' : 'Error'}
                </h3>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearError}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
              
              <p className={`text-sm mt-1 ${
                errorState.errorType === 'quota' 
                  ? 'text-red-700'
                  : errorState.errorType === 'network'
                  ? 'text-yellow-700'
                  : 'text-red-700'
              }`}>
                {errorState.message}
              </p>

              {/* Suggestions */}
              {errorState.suggestions.length > 0 && (
                <div className="mt-2">
                  <p className={`text-xs font-medium ${
                    errorState.errorType === 'quota' 
                      ? 'text-red-800'
                      : errorState.errorType === 'network'
                      ? 'text-yellow-800'
                      : 'text-red-800'
                  }`}>
                    Suggested actions:
                  </p>
                  <ul className={`text-xs mt-1 list-disc list-inside ${
                    errorState.errorType === 'quota' 
                      ? 'text-red-700'
                      : errorState.errorType === 'network'
                      ? 'text-yellow-700'
                      : 'text-red-700'
                  }`}>
                    {errorState.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action buttons */}
              <div className="mt-3 flex space-x-2">
                {errorState.isRetryable && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRefresh}
                    className={
                      errorState.errorType === 'quota' 
                        ? 'text-red-700 border-red-300 hover:bg-red-100'
                        : errorState.errorType === 'network'
                        ? 'text-yellow-700 border-yellow-300 hover:bg-yellow-100'
                        : 'text-red-700 border-red-300 hover:bg-red-100'
                    }
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Retry
                  </Button>
                )}
                
                {errorState.showContactAdmin && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleContactAdmin}
                    className={
                      errorState.errorType === 'quota' 
                        ? 'text-red-700 border-red-300 hover:bg-red-100'
                        : 'text-red-700 border-red-300 hover:bg-red-100'
                    }
                  >
                    <Mail className="h-3 w-3 mr-1" />
                    Contact Admin
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Service readiness warning */}
      {!isServiceReady && !isLoadingData && !errorState.hasError && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mx-4 mt-4 rounded">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-yellow-400 mr-2" />
            <div>
              <p className="text-sm text-yellow-700">
                Chat service is not ready. {quotaInfo?.quota_exceeded 
                  ? 'Your department quota has been exceeded.' 
                  : 'No LLM models are available.'}
              </p>
              <p className="text-xs text-yellow-600 mt-1">
                Please contact your administrator or try refreshing the page.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Chat container */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
        <Card className="flex-1 flex flex-col m-4 shadow-sm">
          {/* Messages */}
          <MessageList
            messages={conversation.messages}
            isLoading={isSending}
          />
          
          {/* Enhanced Input with quota-aware functionality */}
          <MessageInput
            onSendMessage={handleSendMessage}
            disabled={!canSendMessage}
            isLoading={isSending}
            placeholder={
              !isServiceReady
                ? "Chat is currently unavailable..."
                : quotaInfo?.quota_exceeded
                ? "Quota exceeded - cannot send messages..."
                : errorState.hasError && errorState.errorType === 'quota'
                ? "Quota issue - check details above..."
                : !currentModel?.enabled
                ? "Selected model is disabled..."
                : "Ask me anything..."
            }
          />
        </Card>
      </div>

      {/* Enhanced Footer info with quota details */}
      <div className="flex-shrink-0 bg-gray-100 px-4 py-2 text-center text-xs text-gray-500">
        <div className="flex items-center justify-center space-x-4">
          <span>Connected as {user?.username}</span>
          <span>•</span>
          <span>{conversation.messages.length} messages</span>
          {quotaInfo && (
            <>
              <span>•</span>
              <span>
                {quotaInfo.remaining_tokens.toLocaleString()} tokens remaining
              </span>
              <span>•</span>
              <span className={
                quotaInfo.quota_exceeded 
                  ? 'text-red-600 font-medium'
                  : quotaInfo.usage_percentage >= 80
                  ? 'text-yellow-600 font-medium'
                  : 'text-green-600'
              }>
                {quotaInfo.usage_percentage.toFixed(1)}% used
              </span>
            </>
          )}
          {lastQuotaCheck && (
            <>
              <span>•</span>
              <span>
                Last updated: {new Date(lastQuotaCheck).toLocaleTimeString()}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
