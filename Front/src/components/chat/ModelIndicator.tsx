/**
 * ModelIndicator component to show active LLM model
 * Enhanced for AID-US-007 Phase 2: Improved quota status integration
 */

import React, { useState } from 'react';
import { ModelInfo, UsageQuotaInfo } from '../../types/chat';
import { 
  Brain, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  ChevronDown,
  ChevronUp,
  HelpCircle
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import QuotaStatusIndicator from './QuotaStatusIndicator';

interface ModelIndicatorProps {
  currentModel: ModelInfo | null;
  quotaInfo: UsageQuotaInfo | null;
  isLoading?: boolean;
  showQuotaDetails?: boolean;
  onQuotaRefresh?: () => void;
  onContactAdmin?: () => void;
}

const ModelIndicator: React.FC<ModelIndicatorProps> = ({
  currentModel,
  quotaInfo,
  isLoading = false,
  showQuotaDetails = true,
  onQuotaRefresh,
  onContactAdmin
}) => {
  const [showExpandedQuota, setShowExpandedQuota] = useState(false);

  const getProviderIcon = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return '🤖';
      case 'anthropic':
        return '🧠';
      case 'ollama':
        return '🦙';
      case 'azure_openai':
        return '☁️';
      default:
        return '🤖';
    }
  };

  const getQuotaStatus = () => {
    if (!quotaInfo) return { color: 'text-gray-500', icon: null, text: 'Loading...' };
    
    if (quotaInfo.quota_exceeded) {
      return {
        color: 'text-red-600',
        icon: <AlertTriangle className="h-4 w-4" />,
        text: 'Quota Exceeded'
      };
    }
    
    if (quotaInfo.usage_percentage >= 90) {
      return {
        color: 'text-red-600',
        icon: <AlertTriangle className="h-4 w-4" />,
        text: 'Quota Critical'
      };
    }
    
    if (quotaInfo.usage_percentage >= 80) {
      return {
        color: 'text-yellow-600',
        icon: <AlertTriangle className="h-4 w-4" />,
        text: 'Quota Warning'
      };
    }
    
    return {
      color: 'text-green-600',
      icon: <CheckCircle className="h-4 w-4" />,
      text: 'Quota Healthy'
    };
  };

  const quotaStatus = getQuotaStatus();

  if (isLoading) {
    return (
      <Card className="border-b border-gray-200 rounded-none">
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-gray-200 rounded animate-pulse" />
              <div className="w-24 h-4 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="w-16 h-4 bg-gray-200 rounded animate-pulse" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!currentModel) {
    return (
      <Card className="border-b border-gray-200 rounded-none bg-yellow-50">
        <CardContent className="p-3">
          <div className="flex items-center justify-center space-x-2 text-yellow-700">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-sm font-medium">No model available</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="border-b border-gray-200">
      {/* Main model indicator */}
      <Card className="rounded-none border-0 border-b border-gray-200">
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            {/* Model information */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{getProviderIcon(currentModel.provider)}</span>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {currentModel.model_name}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {currentModel.provider}
                    </Badge>
                    {!currentModel.enabled && (
                      <Badge variant="destructive" className="text-xs">
                        Disabled
                      </Badge>
                    )}
                  </div>
                  {currentModel.description && (
                    <div className="text-xs text-gray-500 mt-1">
                      {currentModel.description}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Compact quota status */}
            <div className="flex items-center space-x-4">
              {quotaInfo && (
                <QuotaStatusIndicator
                  quotaInfo={quotaInfo}
                  isLoading={isLoading}
                  showDetails={false}
                  onRefresh={onQuotaRefresh}
                  onContactAdmin={onContactAdmin}
                  compact={true}
                />
              )}
              
              {/* Expand/collapse button for quota details */}
              {showQuotaDetails && quotaInfo && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowExpandedQuota(!showExpandedQuota)}
                  className="h-8 w-8 p-0"
                >
                  {showExpandedQuota ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              )}
            </div>
          </div>

          {/* Model capabilities */}
          {currentModel.capabilities && Object.keys(currentModel.capabilities).length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-100">
              <div className="flex flex-wrap gap-1">
                {Object.entries(currentModel.capabilities).map(([key, value]) => (
                  value && (
                    <span
                      key={key}
                      className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                    >
                      {key.replace('_', ' ')}
                    </span>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Usage warning for disabled model */}
          {!currentModel.enabled && (
            <div className="mt-2 pt-2 border-t border-gray-100">
              <div className="flex items-center space-x-2 text-yellow-700 bg-yellow-50 p-2 rounded">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                <span className="text-xs">
                  This model is currently disabled. Chat functionality may be limited.
                </span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Expanded quota details */}
      {showExpandedQuota && showQuotaDetails && quotaInfo && (
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="p-3">
            <QuotaStatusIndicator
              quotaInfo={quotaInfo}
              isLoading={isLoading}
              showDetails={true}
              onRefresh={onQuotaRefresh}
              onContactAdmin={onContactAdmin}
              compact={false}
            />
          </div>
        </div>
      )}

      {/* Error state for quota unavailable */}
      {showQuotaDetails && !quotaInfo && !isLoading && (
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="p-3">
            <div className="flex items-center space-x-2 text-gray-500">
              <HelpCircle className="h-4 w-4" />
              <span className="text-sm">Quota information unavailable</span>
              {onQuotaRefresh && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onQuotaRefresh}
                  className="ml-auto"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Retry
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelIndicator;
