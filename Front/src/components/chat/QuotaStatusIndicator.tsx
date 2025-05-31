/**
 * QuotaStatusIndicator component for real-time quota monitoring
 * AID-US-007 Phase 2: Enhanced quota status display with warnings and actions
 */

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  HelpCircle, 
  Mail,
  Clock,
  TrendingUp
} from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { UsageQuotaInfo } from '../../types/chat';

interface QuotaStatusIndicatorProps {
  quotaInfo: UsageQuotaInfo | null;
  isLoading?: boolean;
  showDetails?: boolean;
  onRefresh?: () => void;
  onContactAdmin?: () => void;
  compact?: boolean;
}

const QuotaStatusIndicator: React.FC<QuotaStatusIndicatorProps> = ({
  quotaInfo,
  isLoading = false,
  showDetails = true,
  onRefresh,
  onContactAdmin,
  compact = false
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Determine quota status and styling
  const getQuotaStatus = () => {
    if (!quotaInfo) {
      return {
        status: 'unavailable',
        color: 'text-gray-500',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200',
        icon: <HelpCircle className="h-4 w-4" />,
        text: 'Quota Unavailable',
        description: 'Unable to retrieve quota information'
      };
    }

    if (quotaInfo.quota_exceeded) {
      return {
        status: 'exceeded',
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        icon: <XCircle className="h-4 w-4" />,
        text: 'Quota Exceeded',
        description: 'Monthly usage limit has been reached'
      };
    }

    if (quotaInfo.usage_percentage >= 90) {
      return {
        status: 'critical',
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        icon: <AlertTriangle className="h-4 w-4" />,
        text: 'Quota Critical',
        description: 'Very close to monthly limit'
      };
    }

    if (quotaInfo.usage_percentage >= 80) {
      return {
        status: 'warning',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        icon: <AlertTriangle className="h-4 w-4" />,
        text: 'Quota Warning',
        description: 'Approaching monthly limit'
      };
    }

    return {
      status: 'healthy',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      icon: <CheckCircle className="h-4 w-4" />,
      text: 'Quota Healthy',
      description: 'Well within monthly limits'
    };
  };

  const status = getQuotaStatus();

  // Format numbers for display
  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  // Calculate estimated days remaining
  const getEstimatedDaysRemaining = (): string => {
    if (!quotaInfo || quotaInfo.quota_exceeded || quotaInfo.remaining_tokens <= 0) {
      return 'N/A';
    }

    // Simple estimation based on current usage pattern
    const daysInMonth = 30;
    const currentDay = new Date().getDate();
    const dailyUsage = quotaInfo.current_usage / currentDay;
    
    if (dailyUsage <= 0) return '30+ days';
    
    const daysRemaining = Math.floor(quotaInfo.remaining_tokens / dailyUsage);
    return daysRemaining > 30 ? '30+ days' : `~${daysRemaining} days`;
  };

  // Compact view for space-constrained areas
  if (compact) {
    return (
      <div 
        className={`flex items-center space-x-2 px-2 py-1 rounded-md ${status.bgColor} ${status.borderColor} border`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        <div className={status.color}>
          {isLoading ? (
            <RefreshCw className="h-3 w-3 animate-spin" />
          ) : (
            status.icon
          )}
        </div>
        
        {quotaInfo && (
          <div className="text-xs">
            <span className={`font-medium ${status.color}`}>
              {quotaInfo.usage_percentage.toFixed(0)}%
            </span>
            <span className="text-gray-500 ml-1">
              ({formatNumber(quotaInfo.remaining_tokens)} left)
            </span>
          </div>
        )}

        {/* Tooltip for compact view */}
        {showTooltip && quotaInfo && (
          <div className="absolute z-50 bg-black text-white text-xs rounded px-2 py-1 -mt-8 ml-4">
            {status.description}: {formatNumber(quotaInfo.current_usage)}/{formatNumber(quotaInfo.monthly_limit)} tokens
          </div>
        )}
      </div>
    );
  }

  // Full detailed view
  return (
    <Card className={`${status.borderColor} border-l-4`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Status header */}
          <div className="flex items-center space-x-3">
            <div className={status.color}>
              {isLoading ? (
                <RefreshCw className="h-5 w-5 animate-spin" />
              ) : (
                status.icon
              )}
            </div>
            
            <div>
              <div className="flex items-center space-x-2">
                <h3 className={`font-medium ${status.color}`}>
                  {status.text}
                </h3>
                <Badge 
                  variant={status.status === 'exceeded' ? 'destructive' : 
                           status.status === 'warning' || status.status === 'critical' ? 'default' : 'secondary'}
                >
                  {quotaInfo ? `${quotaInfo.usage_percentage.toFixed(1)}%` : 'N/A'}
                </Badge>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {status.description}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center space-x-2">
            {onRefresh && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRefresh}
                disabled={isLoading}
                className="h-8 px-2"
              >
                <RefreshCw className={`h-3 w-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            )}
            
            {onContactAdmin && (status.status === 'exceeded' || status.status === 'critical') && (
              <Button
                variant="outline"
                size="sm"
                onClick={onContactAdmin}
                className="h-8 px-2"
              >
                <Mail className="h-3 w-3 mr-1" />
                Contact Admin
              </Button>
            )}
          </div>
        </div>

        {/* Detailed quota information */}
        {showDetails && quotaInfo && (
          <div className="mt-4 space-y-3">
            {/* Usage progress bar */}
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Usage Progress</span>
                <span>
                  {formatNumber(quotaInfo.current_usage)} / {formatNumber(quotaInfo.monthly_limit)} tokens
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    quotaInfo.quota_exceeded
                      ? 'bg-red-500'
                      : quotaInfo.usage_percentage >= 80
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{
                    width: `${Math.min(quotaInfo.usage_percentage, 100)}%`
                  }}
                />
              </div>
            </div>

            {/* Quota statistics grid */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-gray-600">Remaining</p>
                  <p className="font-medium">
                    {formatNumber(quotaInfo.remaining_tokens)} tokens
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4 text-gray-400" />
                <div>
                  <p className="text-gray-600">Estimated Time</p>
                  <p className="font-medium">
                    {getEstimatedDaysRemaining()}
                  </p>
                </div>
              </div>
            </div>

            {/* Department info */}
            <div className="pt-2 border-t border-gray-100">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Department: {quotaInfo.department_name}</span>
                <span>Monthly quota resets on the 1st</span>
              </div>
            </div>

            {/* Warning or error messages */}
            {quotaInfo.quota_exceeded && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <div className="flex items-start space-x-2">
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-medium text-red-800">Quota Exceeded</p>
                    <p className="text-red-700 mt-1">
                      Your department has used all available tokens for this month. 
                      New requests cannot be processed until the quota resets next month.
                    </p>
                    <div className="mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={onContactAdmin}
                        className="text-red-700 border-red-300 hover:bg-red-100"
                      >
                        Request Quota Increase
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {quotaInfo.usage_percentage >= 80 && !quotaInfo.quota_exceeded && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="font-medium text-yellow-800">Approaching Quota Limit</p>
                    <p className="text-yellow-700 mt-1">
                      You're using {quotaInfo.usage_percentage.toFixed(1)}% of your monthly quota. 
                      Consider monitoring your usage to avoid hitting the limit.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default QuotaStatusIndicator;
