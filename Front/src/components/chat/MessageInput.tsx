/**
 * MessageInput component for user input
 * Enhanced for AID-US-007 Phase 2: Quota-aware input with improved guidance
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertTriangle, Clock, HelpCircle } from 'lucide-react';
import { Button } from '../ui/button';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  quotaInfo?: {
    quota_exceeded: boolean;
    usage_percentage: number;
    remaining_tokens: number;
    monthly_limit: number;
  } | null;
  onContactAdmin?: () => void;
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  disabled = false,
  isLoading = false,
  placeholder = "Type your message here...",
  quotaInfo,
  onContactAdmin
}) => {
  const [message, setMessage] = useState('');
  const [showQuotaWarning, setShowQuotaWarning] = useState(false);
  const [estimatedTokens, setEstimatedTokens] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Estimate tokens for current message (rough approximation: ~4 characters per token)
  useEffect(() => {
    const estimated = Math.ceil(message.length / 4);
    setEstimatedTokens(estimated);
    
    // Show quota warning if approaching limits
    if (quotaInfo && !quotaInfo.quota_exceeded && estimated > 0) {
      const wouldExceedWarning = quotaInfo.usage_percentage >= 90 || 
                                quotaInfo.remaining_tokens < estimated * 2;
      setShowQuotaWarning(wouldExceedWarning);
    } else {
      setShowQuotaWarning(false);
    }
  }, [message, quotaInfo]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const trimmedMessage = message.trim();
    if (trimmedMessage && !disabled && !isLoading) {
      onSendMessage(trimmedMessage);
      setMessage('');
      setShowQuotaWarning(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [message]);

  // Focus on mount
  useEffect(() => {
    if (!disabled && !quotaInfo?.quota_exceeded) {
      textareaRef.current?.focus();
    }
  }, [disabled, quotaInfo?.quota_exceeded]);

  // Get quota status for styling and messaging
  const getQuotaStatus = () => {
    if (!quotaInfo) return null;
    
    if (quotaInfo.quota_exceeded) {
      return {
        type: 'exceeded',
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-300',
        message: 'Monthly quota exceeded - cannot send messages'
      };
    }
    
    if (quotaInfo.usage_percentage >= 95) {
      return {
        type: 'critical',
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-300',
        message: `Critical: Only ${quotaInfo.remaining_tokens.toLocaleString()} tokens remaining`
      };
    }
    
    if (quotaInfo.usage_percentage >= 80) {
      return {
        type: 'warning',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-300',
        message: `Warning: ${quotaInfo.remaining_tokens.toLocaleString()} tokens remaining this month`
      };
    }
    
    return null;
  };

  const quotaStatus = getQuotaStatus();
  const isQuotaBlocked = quotaInfo?.quota_exceeded || false;
  const showTokenEstimate = message.length > 50 && estimatedTokens > 0;

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Quota warning banner */}
      {quotaStatus && (
        <div className={`px-4 py-2 ${quotaStatus.bgColor} border-b ${quotaStatus.borderColor}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className={`h-4 w-4 ${quotaStatus.color}`} />
              <span className={`text-sm font-medium ${quotaStatus.color}`}>
                {quotaStatus.message}
              </span>
            </div>
            
            {quotaStatus.type === 'exceeded' && onContactAdmin && (
              <Button
                variant="outline"
                size="sm"
                onClick={onContactAdmin}
                className={`${quotaStatus.color} border-current hover:bg-white/50`}
              >
                Contact Admin
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Token usage warning for current message */}
      {showQuotaWarning && quotaInfo && !quotaInfo.quota_exceeded && (
        <div className="px-4 py-2 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-center space-x-2 text-sm text-yellow-700">
            <Clock className="h-4 w-4" />
            <span>
              This message (~{estimatedTokens} tokens) will use{' '}
              {quotaInfo.remaining_tokens > 0 
                ? `${((estimatedTokens / quotaInfo.remaining_tokens) * 100).toFixed(1)}%`
                : 'more than'
              } of your remaining quota
            </span>
          </div>
        </div>
      )}

      {/* Main input area */}
      <div className="p-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || isLoading || isQuotaBlocked}
              className={
                "w-full resize-none rounded-lg border px-3 py-2 " +
                "focus:outline-none focus:ring-1 transition-colors duration-200 " +
                (disabled || isLoading || isQuotaBlocked
                  ? "bg-gray-50 text-gray-500 cursor-not-allowed border-gray-300"
                  : quotaStatus?.type === 'exceeded'
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                  : quotaStatus?.type === 'critical'
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500"
                  : quotaStatus?.type === 'warning'
                  ? "border-yellow-300 focus:border-yellow-500 focus:ring-yellow-500"
                  : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                )
              }
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
            
            {/* Input footer with character count and guidance */}
            <div className="flex justify-between items-center mt-2 text-xs">
              <div className="flex items-center space-x-4">
                {/* Character counter */}
                {message.length > 0 && (
                  <span className={message.length > 10000 ? 'text-red-500' : 'text-gray-500'}>
                    {message.length.toLocaleString()}/10,000 characters
                  </span>
                )}
                
                {/* Token estimate */}
                {showTokenEstimate && (
                  <span className="text-gray-500">
                    ~{estimatedTokens} tokens
                  </span>
                )}
                
                {/* Quota remaining */}
                {quotaInfo && !quotaInfo.quota_exceeded && (
                  <span className={
                    quotaInfo.remaining_tokens < 1000 
                      ? 'text-red-500 font-medium'
                      : quotaInfo.remaining_tokens < 5000
                      ? 'text-yellow-600'
                      : 'text-gray-500'
                  }>
                    {quotaInfo.remaining_tokens.toLocaleString()} tokens left
                  </span>
                )}
              </div>
              
              {/* Input shortcuts */}
              <div className="hidden sm:block text-gray-400">
                {!disabled && !isQuotaBlocked && (
                  <span>Press Enter to send • Shift+Enter for new line</span>
                )}
              </div>
            </div>
          </div>
          
          <Button
            type="submit"
            disabled={!message.trim() || disabled || isLoading || message.length > 10000 || isQuotaBlocked}
            className={
              "px-4 py-2 h-auto min-h-[40px] " +
              (quotaStatus?.type === 'exceeded' 
                ? 'opacity-50 cursor-not-allowed'
                : ''
              )
            }
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Sending...
              </>
            ) : isQuotaBlocked ? (
              <>
                <AlertTriangle className="h-4 w-4 mr-2" />
                Blocked
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Send
              </>
            )}
          </Button>
        </form>
        
        {/* Helpful tips based on state */}
        {message.length === 0 && !disabled && !isQuotaBlocked && (
          <div className="mt-3 text-xs text-gray-400 text-center">
            💡 Tip: Ask questions, request explanations, or start a conversation with the AI
          </div>
        )}
        
        {/* Quota exceeded guidance */}
        {isQuotaBlocked && (
          <div className="mt-3 text-xs text-center">
            <div className="inline-flex items-center space-x-2 px-3 py-2 bg-red-50 text-red-700 rounded-md">
              <HelpCircle className="h-4 w-4" />
              <span>
                Your department has exceeded its monthly quota. Messages will be enabled when the quota resets next month.
              </span>
            </div>
          </div>
        )}
        
        {/* Critical quota warning */}
        {quotaStatus?.type === 'critical' && !isQuotaBlocked && (
          <div className="mt-3 text-xs text-center">
            <div className="inline-flex items-center space-x-2 px-3 py-2 bg-yellow-50 text-yellow-700 rounded-md">
              <AlertTriangle className="h-4 w-4" />
              <span>
                Very low quota remaining. Consider shorter messages to avoid hitting the limit.
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageInput;
