/**
 * UsageMonitoring component for admin dashboard
 * AID-US-007 Phase 3: Real-time usage monitoring and analytics
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  Activity,
  Users,
  Zap,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  Filter,
  Eye,
  Clock,
  BarChart3,
  PieChart,
  Calendar,
  Search
} from 'lucide-react';
import {
  UsageMonitoringProps,
  UsageMonitoringDashboard,
  DepartmentUsageStats,
  UserUsageStats,
  ModelUsageStats,
  UsageAlert,
  RealTimeUsageMetrics,
  UsageMonitoringFilters
} from '../../types/admin';
import { adminService } from '../../services/adminService';

export const UsageMonitoring: React.FC<UsageMonitoringProps> = ({
  onError,
  onSuccess,
  onClearMessages
}) => {
  const [dashboard, setDashboard] = useState<UsageMonitoringDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [filters, setFilters] = useState<UsageMonitoringFilters>({});
  const [selectedView, setSelectedView] = useState<'overview' | 'departments' | 'users' | 'models' | 'alerts'>('overview');

  // Auto-refresh interval
  useEffect(() => {
    loadDashboard();
    
    // Set up auto-refresh every 30 seconds for real-time metrics
    const interval = setInterval(() => {
      if (selectedView === 'overview') {
        refreshRealTimeMetrics();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedTimeRange, filters, selectedView]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      // Simulate API call - in real implementation would call backend
      const mockDashboard: UsageMonitoringDashboard = {
        overview_stats: {
          total_requests: 15623,
          total_tokens_used: 2847391,
          total_cost_estimated: 156.78,
          unique_users: 47,
          active_departments: 8,
          active_models: 5,
          avg_tokens_per_request: 182.3,
          avg_cost_per_request: 0.0100,
          peak_usage_hour: 14,
          requests_last_24h: 1247,
          tokens_last_24h: 227156
        },
        real_time_metrics: {
          current_active_users: 12,
          requests_per_minute: 4.2,
          tokens_per_minute: 765,
          avg_response_time_ms: 1850,
          error_rate_percentage: 2.1,
          quota_alerts_count: 3,
          system_health_score: 94,
          last_updated: new Date().toISOString()
        },
        department_stats: [
          {
            department_id: '1',
            department_name: 'Engineering',
            total_requests: 8942,
            total_tokens_used: 1623847,
            total_cost_estimated: 89.31,
            unique_users: 23,
            quota_usage_percentage: 78.5,
            quota_limit_tokens: 2000000,
            is_quota_exceeded: false,
            is_warning_threshold_reached: false,
            last_activity: new Date(Date.now() - 300000).toISOString(),
            top_users: [
              { username: 'john.doe', tokens_used: 156789, requests: 1247 },
              { username: 'jane.smith', tokens_used: 142356, requests: 1156 }
            ]
          },
          {
            department_id: '2',
            department_name: 'Marketing',
            total_requests: 3421,
            total_tokens_used: 621394,
            total_cost_estimated: 34.16,
            unique_users: 12,
            quota_usage_percentage: 95.2,
            quota_limit_tokens: 650000,
            is_quota_exceeded: false,
            is_warning_threshold_reached: true,
            last_activity: new Date(Date.now() - 120000).toISOString(),
            top_users: [
              { username: 'mike.johnson', tokens_used: 89234, requests: 567 }
            ]
          },
          {
            department_id: '3',
            department_name: 'Sales',
            total_requests: 2156,
            total_tokens_used: 389572,
            total_cost_estimated: 21.43,
            unique_users: 8,
            quota_usage_percentage: 102.1,
            quota_limit_tokens: 380000,
            is_quota_exceeded: true,
            is_warning_threshold_reached: true,
            last_activity: new Date(Date.now() - 600000).toISOString(),
            top_users: [
              { username: 'sarah.wilson', tokens_used: 67891, requests: 423 }
            ]
          }
        ],
        top_users: [
          {
            user_id: '1',
            username: 'john.doe',
            department_name: 'Engineering',
            total_requests: 1247,
            total_tokens_used: 156789,
            total_cost_estimated: 8.62,
            avg_tokens_per_request: 125.7,
            last_activity: new Date(Date.now() - 180000).toISOString(),
            most_used_model: 'gpt-4',
            requests_by_model: { 'gpt-4': 892, 'gpt-3.5-turbo': 355 }
          }
        ],
        model_stats: [
          {
            llm_config_id: '1',
            model_name: 'gpt-4',
            provider: 'openai',
            total_requests: 9847,
            total_tokens_used: 1789234,
            total_cost_estimated: 98.45,
            unique_users: 34,
            avg_tokens_per_request: 181.7,
            last_used: new Date(Date.now() - 60000).toISOString(),
            requests_by_department: { 'Engineering': 5234, 'Marketing': 2413, 'Sales': 1200 },
            usage_trend: [
              { date: '2025-05-29', requests: 1247, tokens: 226789 },
              { date: '2025-05-30', requests: 1389, tokens: 252156 }
            ]
          }
        ],
        recent_alerts: [
          {
            id: '1',
            alert_type: 'quota_exceeded',
            title: 'Sales Department Quota Exceeded',
            message: 'Sales department has exceeded their monthly token quota by 2.1%',
            severity: 'high',
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            is_read: false,
            related_department: 'Sales',
            action_required: true,
            metadata: { quota_percentage: 102.1 }
          },
          {
            id: '2',
            alert_type: 'quota_warning',
            title: 'Marketing Department Approaching Quota',
            message: 'Marketing department has used 95.2% of their monthly quota',
            severity: 'medium',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            is_read: false,
            related_department: 'Marketing',
            action_required: false,
            metadata: { quota_percentage: 95.2 }
          }
        ],
        usage_trends: {
          requests_trend: {
            current_period: 1247,
            previous_period: 1089,
            percentage_change: 14.5,
            trend_direction: 'up'
          },
          tokens_trend: {
            current_period: 227156,
            previous_period: 198734,
            percentage_change: 14.3,
            trend_direction: 'up'
          },
          cost_trend: {
            current_period: 12.48,
            previous_period: 10.93,
            percentage_change: 14.2,
            trend_direction: 'up'
          },
          users_trend: {
            current_period: 47,
            previous_period: 43,
            percentage_change: 9.3,
            trend_direction: 'up'
          }
        },
        timeseries_data: [],
        quota_summary: {
          total_quotas: 12,
          quotas_exceeded: 1,
          quotas_at_warning: 2,
          departments_with_quotas: 8,
          llm_configs_with_quotas: 5,
          average_usage_percentage: 76.3,
          top_usage_departments: [],
          quota_enforcement_breakdown: { hard_block: 8, soft_warning: 4 }
        }
      };

      setDashboard(mockDashboard);
    } catch (error) {
      console.error('Error loading usage dashboard:', error);
      onError('Failed to load usage monitoring dashboard');
    } finally {
      setLoading(false);
    }
  };

  const refreshRealTimeMetrics = async () => {
    try {
      setRefreshing(true);
      // In real implementation, would call specific endpoint for real-time metrics
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call
      // Update only real-time metrics without full reload
    } catch (error) {
      console.error('Error refreshing real-time metrics:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExportUsage = async () => {
    try {
      onSuccess('Usage data export started. You will receive a download link via email.');
    } catch (error) {
      onError('Failed to export usage data');
    }
  };

  const handleMarkAlertAsRead = async (alertId: string) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 300));
      onSuccess('Alert marked as read');
    } catch (error) {
      onError('Failed to mark alert as read');
    }
  };

  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  const formatPercentage = (percent: number): string => {
    return `${percent.toFixed(1)}%`;
  };

  const getTrendIcon = (direction: 'up' | 'down' | 'stable') => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getQuotaStatusColor = (percentage: number, isExceeded: boolean) => {
    if (isExceeded) return 'text-red-600';
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Usage Monitoring</h2>
            <p className="text-muted-foreground">Loading usage analytics...</p>
          </div>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Loading...</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Usage Data Available</h3>
            <p className="text-muted-foreground mb-4">
              Unable to load usage monitoring data. Please try refreshing.
            </p>
            <Button onClick={loadDashboard}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Usage Monitoring</h2>
          <p className="text-muted-foreground">
            Real-time monitoring and analytics for LLM usage across departments
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refreshRealTimeMetrics}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportUsage}
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* View Selector */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { key: 'overview', label: 'Overview', icon: BarChart3 },
          { key: 'departments', label: 'Departments', icon: Users },
          { key: 'users', label: 'Users', icon: Activity },
          { key: 'models', label: 'Models', icon: Zap },
          { key: 'alerts', label: 'Alerts', icon: AlertTriangle }
        ].map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSelectedView(key as any)}
            className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedView === key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Icon className="h-4 w-4 mr-2" />
            {label}
          </button>
        ))}
      </div>

      {/* Overview Stats */}
      {selectedView === 'overview' && (
        <>
          {/* Real-time Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.real_time_metrics.current_active_users}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  {getTrendIcon(dashboard.usage_trends.users_trend.trend_direction)}
                  <span className="ml-1">{formatPercentage(dashboard.usage_trends.users_trend.percentage_change)} from yesterday</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Requests/Min</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.real_time_metrics.requests_per_minute.toFixed(1)}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  {getTrendIcon(dashboard.usage_trends.requests_trend.trend_direction)}
                  <span className="ml-1">{formatPercentage(dashboard.usage_trends.requests_trend.percentage_change)} from yesterday</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Tokens/Min</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatNumber(dashboard.real_time_metrics.tokens_per_minute)}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  {getTrendIcon(dashboard.usage_trends.tokens_trend.trend_direction)}
                  <span className="ml-1">{formatPercentage(dashboard.usage_trends.tokens_trend.percentage_change)} from yesterday</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">System Health</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{dashboard.real_time_metrics.system_health_score}%</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  <div className={`w-2 h-2 rounded-full mr-2 ${
                    dashboard.real_time_metrics.system_health_score >= 95 ? 'bg-green-500' :
                    dashboard.real_time_metrics.system_health_score >= 85 ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <span>
                    {dashboard.real_time_metrics.system_health_score >= 95 ? 'Excellent' :
                     dashboard.real_time_metrics.system_health_score >= 85 ? 'Good' : 'Needs Attention'}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 24h Summary */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">24h Requests</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{formatNumber(dashboard.overview_stats.requests_last_24h)}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  Avg {dashboard.overview_stats.avg_tokens_per_request.toFixed(0)} tokens per request
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">24h Tokens</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">{formatNumber(dashboard.overview_stats.tokens_last_24h)}</div>
                <p className="text-sm text-muted-foreground mt-1">
                  Peak usage at {dashboard.overview_stats.peak_usage_hour}:00
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">24h Cost</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-purple-600">
                  {formatCurrency(dashboard.usage_trends.cost_trend.current_period)}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Avg {formatCurrency(dashboard.overview_stats.avg_cost_per_request)} per request
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}

      {/* Department Stats */}
      {selectedView === 'departments' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Department Usage Statistics</h3>
            <Badge variant="outline">
              {dashboard.department_stats.length} departments
            </Badge>
          </div>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {dashboard.department_stats.map((dept) => (
              <Card key={dept.department_id} className="relative">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{dept.department_name}</CardTitle>
                    {dept.is_quota_exceeded && (
                      <Badge variant="destructive" className="text-xs">
                        Exceeded
                      </Badge>
                    )}
                    {dept.is_warning_threshold_reached && !dept.is_quota_exceeded && (
                      <Badge variant="default" className="text-xs bg-yellow-500">
                        Warning
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-muted-foreground">Requests:</span>
                      <div className="font-medium">{formatNumber(dept.total_requests)}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Users:</span>
                      <div className="font-medium">{dept.unique_users}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Tokens:</span>
                      <div className="font-medium">{formatNumber(dept.total_tokens_used)}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Cost:</span>
                      <div className="font-medium">{formatCurrency(dept.total_cost_estimated)}</div>
                    </div>
                  </div>
                  
                  {/* Quota usage bar */}
                  <div>
                    <div className="flex justify-between text-xs text-muted-foreground mb-1">
                      <span>Quota Usage</span>
                      <span className={getQuotaStatusColor(dept.quota_usage_percentage, dept.is_quota_exceeded)}>
                        {formatPercentage(dept.quota_usage_percentage)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all duration-300 ${
                          dept.is_quota_exceeded
                            ? 'bg-red-500'
                            : dept.quota_usage_percentage >= 90
                            ? 'bg-red-500'
                            : dept.quota_usage_percentage >= 80
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}
                        style={{
                          width: `${Math.min(dept.quota_usage_percentage, 100)}%`
                        }}
                      />
                    </div>
                  </div>

                  {/* Last activity */}
                  <div className="flex items-center text-xs text-muted-foreground">
                    <Clock className="h-3 w-3 mr-1" />
                    <span>Last activity: {new Date(dept.last_activity).toLocaleTimeString()}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      {(selectedView === 'overview' || selectedView === 'alerts') && dashboard.recent_alerts.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Alerts</CardTitle>
              <Badge variant="outline">
                {dashboard.recent_alerts.filter(a => !a.is_read).length} unread
              </Badge>
            </div>
            <CardDescription>
              System alerts and notifications requiring attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboard.recent_alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-start p-3 rounded-lg border transition-colors ${
                    alert.is_read ? 'bg-gray-50' : 'bg-white border-l-4 border-l-blue-500'
                  }`}
                >
                  <div className="flex-shrink-0 mr-3">
                    {alert.severity === 'critical' && <AlertTriangle className="h-5 w-5 text-red-500" />}
                    {alert.severity === 'high' && <AlertTriangle className="h-5 w-5 text-orange-500" />}
                    {alert.severity === 'medium' && <AlertTriangle className="h-5 w-5 text-yellow-500" />}
                    {alert.severity === 'low' && <AlertTriangle className="h-5 w-5 text-blue-500" />}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-sm font-medium text-gray-900">{alert.title}</h4>
                      <div className="flex items-center space-x-2">
                        <Badge 
                          variant={alert.severity === 'critical' || alert.severity === 'high' ? 'destructive' : 'default'}
                          className="text-xs"
                        >
                          {alert.severity}
                        </Badge>
                        {!alert.is_read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleMarkAlertAsRead(alert.id)}
                            className="text-xs"
                          >
                            Mark as read
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center space-x-2">
                        {alert.related_department && (
                          <span>Department: {alert.related_department}</span>
                        )}
                        {alert.related_user && (
                          <span>User: {alert.related_user}</span>
                        )}
                      </div>
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UsageMonitoring;
