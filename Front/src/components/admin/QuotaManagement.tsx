import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { adminService } from '../../services/adminService';
import type { 
  Quota, 
  QuotaCreate, 
  QuotaUpdate, 
  QuotaListResponse,
  Department,
  LLMConfiguration,
  QuotaTemplateSettings,
  QuotaFormData,
  QuotaEnforcement,
  QuotaTemplate,
  QuotaOverviewStats,
  QuotaAlertsResponse,
  BulkQuotaCreate,
  QuotaFilters
} from '../../types/admin';

interface QuotaManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

interface QuotaFormProps {
  mode: 'create' | 'edit';
  initialData?: Quota;
  onSubmit: (data: QuotaCreate | QuotaUpdate) => void;
  onCancel: () => void;
  loading?: boolean;
  departments: Department[];
  llmConfigurations: LLMConfiguration[];
  templates: QuotaTemplateSettings[];
}

function QuotaForm({ 
  mode, 
  initialData, 
  onSubmit, 
  onCancel, 
  loading = false, 
  departments, 
  llmConfigurations, 
  templates 
}: QuotaFormProps) {
  const [formData, setFormData] = useState<QuotaFormData>({
    department_id: initialData?.department_id || '',
    llm_config_id: initialData?.llm_config_id || '',
    monthly_limit_tokens: initialData?.monthly_limit_tokens || 100000,
    daily_limit_tokens: initialData?.daily_limit_tokens || 5000,
    monthly_limit_requests: initialData?.monthly_limit_requests || 1000,
    daily_limit_requests: initialData?.daily_limit_requests || 50,
    enforcement_mode: initialData?.enforcement_mode || 'soft_warning',
    warning_threshold_percent: initialData?.warning_threshold_percent || 80
  });
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const applyTemplate = (templateName: string) => {
    const template = templates.find(t => t.name === templateName);
    if (template) {
      setFormData(prev => ({
        ...prev,
        monthly_limit_tokens: template.monthly_limit_tokens,
        daily_limit_tokens: template.daily_limit_tokens,
        monthly_limit_requests: template.monthly_limit_requests,
        daily_limit_requests: template.daily_limit_requests,
        enforcement_mode: template.enforcement_mode,
        warning_threshold_percent: template.warning_threshold_percent
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.department_id || !formData.llm_config_id) {
      return;
    }

    if (mode === 'create') {
      const createData: QuotaCreate = {
        department_id: formData.department_id,
        llm_config_id: formData.llm_config_id,
        monthly_limit_tokens: formData.monthly_limit_tokens,
        daily_limit_tokens: formData.daily_limit_tokens,
        monthly_limit_requests: formData.monthly_limit_requests,
        daily_limit_requests: formData.daily_limit_requests,
        enforcement_mode: formData.enforcement_mode,
        warning_threshold_percent: formData.warning_threshold_percent
      };
      onSubmit(createData);
    } else {
      const updateData: QuotaUpdate = {
        monthly_limit_tokens: formData.monthly_limit_tokens,
        daily_limit_tokens: formData.daily_limit_tokens,
        monthly_limit_requests: formData.monthly_limit_requests,
        daily_limit_requests: formData.daily_limit_requests,
        enforcement_mode: formData.enforcement_mode,
        warning_threshold_percent: formData.warning_threshold_percent
      };
      onSubmit(updateData);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {mode === 'create' ? 'Create New Quota' : 'Edit Quota'}
        </CardTitle>
        <CardDescription>
          {mode === 'create' 
            ? 'Set usage limits for a department and LLM model combination'
            : 'Update quota settings and limits'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Template Selection (only for create mode) */}
          {mode === 'create' && templates.length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="template">Quick Setup Template</Label>
              <select
                id="template"
                value={selectedTemplate}
                onChange={(e) => {
                  setSelectedTemplate(e.target.value);
                  if (e.target.value) {
                    applyTemplate(e.target.value);
                  }
                }}
                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <option value="">Choose a template (optional)</option>
                {templates.map((template) => (
                  <option key={template.name} value={template.name}>
                    {template.name} - {template.description}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Department and LLM Selection */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="department">Department *</Label>
              <select
                id="department"
                value={formData.department_id}
                onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                disabled={mode === 'edit' || loading}
                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
              >
                <option value="">Select department</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="llm_config">LLM Model *</Label>
              <select
                id="llm_config"
                value={formData.llm_config_id}
                onChange={(e) => setFormData({ ...formData, llm_config_id: e.target.value })}
                disabled={mode === 'edit' || loading}
                className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                required
              >
                <option value="">Select LLM model</option>
                {llmConfigurations.map((config) => (
                  <option key={config.id} value={config.id}>
                    {config.model_name} ({config.provider})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Token Limits */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Token Limits</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="monthly_tokens">Monthly Token Limit</Label>
                <Input
                  id="monthly_tokens"
                  type="number"
                  min="0"
                  value={formData.monthly_limit_tokens}
                  onChange={(e) => setFormData({ ...formData, monthly_limit_tokens: parseInt(e.target.value) || 0 })}
                  placeholder="100000"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">0 = unlimited</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="daily_tokens">Daily Token Limit</Label>
                <Input
                  id="daily_tokens"
                  type="number"
                  min="0"
                  value={formData.daily_limit_tokens}
                  onChange={(e) => setFormData({ ...formData, daily_limit_tokens: parseInt(e.target.value) || 0 })}
                  placeholder="5000"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">0 = unlimited</p>
              </div>
            </div>
          </div>

          {/* Request Limits */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Request Limits</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="monthly_requests">Monthly Request Limit</Label>
                <Input
                  id="monthly_requests"
                  type="number"
                  min="0"
                  value={formData.monthly_limit_requests}
                  onChange={(e) => setFormData({ ...formData, monthly_limit_requests: parseInt(e.target.value) || 0 })}
                  placeholder="1000"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">0 = unlimited</p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="daily_requests">Daily Request Limit</Label>
                <Input
                  id="daily_requests"
                  type="number"
                  min="0"
                  value={formData.daily_limit_requests}
                  onChange={(e) => setFormData({ ...formData, daily_limit_requests: parseInt(e.target.value) || 0 })}
                  placeholder="50"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">0 = unlimited</p>
              </div>
            </div>
          </div>

          {/* Enforcement Settings */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium">Enforcement Settings</h4>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="enforcement_mode">Enforcement Mode</Label>
                <select
                  id="enforcement_mode"
                  value={formData.enforcement_mode}
                  onChange={(e) => setFormData({ ...formData, enforcement_mode: e.target.value as QuotaEnforcement })}
                  disabled={loading}
                  className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="soft_warning">Soft Warning - Allow usage with warnings</option>
                  <option value="hard_block">Hard Block - Block usage when exceeded</option>
                </select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="warning_threshold">Warning Threshold (%)</Label>
                <Input
                  id="warning_threshold"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.warning_threshold_percent}
                  onChange={(e) => setFormData({ ...formData, warning_threshold_percent: parseInt(e.target.value) || 80 })}
                  placeholder="80"
                  disabled={loading}
                />
                <p className="text-xs text-gray-500">Percentage at which to show warnings</p>
              </div>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              type="submit" 
              disabled={loading || !formData.department_id || !formData.llm_config_id}
            >
              {loading ? 'Saving...' : (mode === 'create' ? 'Create Quota' : 'Update Quota')}
            </Button>
            <Button 
              type="button" 
              variant="outline" 
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export function QuotaManagement({ onError, onSuccess, onClearMessages }: QuotaManagementProps) {
  const [quotas, setQuotas] = useState<Quota[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [llmConfigurations, setLlmConfigurations] = useState<LLMConfiguration[]>([]);
  const [templates, setTemplates] = useState<QuotaTemplateSettings[]>([]);
  const [overviewStats, setOverviewStats] = useState<QuotaOverviewStats | null>(null);
  const [alerts, setAlerts] = useState<QuotaAlertsResponse | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingQuota, setEditingQuota] = useState<Quota | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  
  const [filters, setFilters] = useState<QuotaFilters>({
    exceeded_only: false,
    warning_only: false
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadQuotas();
  }, [filters, currentPage]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      // Load all required data in parallel
      const [templatesData, deptData, llmData, statsData, alertsData] = await Promise.all([
        adminService.getQuotaTemplates(),
        adminService.getDepartments(),
        adminService.getLLMConfigurations({ enabled_only: true }),
        adminService.getQuotaOverview().catch(() => null), // Handle gracefully if backend not ready
        adminService.getQuotaAlerts(20).catch(() => null) // Handle gracefully if backend not ready
      ]);
      
      setTemplates(templatesData.templates);
      setDepartments(deptData.departments);
      setLlmConfigurations(llmData.configurations);
      if (statsData) setOverviewStats(statsData);
      if (alertsData) setAlerts(alertsData);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load quota data');
    } finally {
      setLoading(false);
    }
  };

  const loadQuotas = async () => {
    try {
      const skip = (currentPage - 1) * pageSize;
      const response = await adminService.getQuotas({
        ...filters,
        skip,
        limit: pageSize
      });
      setQuotas(response.quotas);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load quotas');
    }
  };

  const handleCreateQuota = () => {
    setEditingQuota(null);
    setShowForm(true);
  };

  const handleEditQuota = (quota: Quota) => {
    setEditingQuota(quota);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingQuota(null);
  };

  const handleSubmitForm = async (data: QuotaCreate | QuotaUpdate) => {
    try {
      setFormLoading(true);
      onClearMessages();

      if (editingQuota) {
        await adminService.updateQuota(editingQuota.id, data as QuotaUpdate);
        onSuccess('Quota updated successfully');
      } else {
        await adminService.createQuota(data as QuotaCreate);
        onSuccess('Quota created successfully');
      }

      handleCancelForm();
      loadQuotas();
      loadInitialData(); // Refresh stats
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to save quota');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteQuota = async (quota: Quota) => {
    if (window.confirm(`Are you sure you want to delete the quota for "${quota.department_name}" using "${quota.llm_model_name}"? This action cannot be undone.`)) {
      try {
        await adminService.deleteQuota(quota.id);
        onSuccess('Quota deleted successfully');
        loadQuotas();
        loadInitialData(); // Refresh stats
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Failed to delete quota');
      }
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getUsageBadgeVariant = (percentage: number, isExceeded: boolean) => {
    if (isExceeded) return 'destructive';
    if (percentage >= 80) return 'secondary';
    return 'default';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading quota management...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Quota Management</h2>
          <p className="text-gray-500">
            Set and manage department usage quotas for LLM models
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleCreateQuota} disabled={showForm}>
            Add Quota
          </Button>
        </div>
      </div>

      {/* Overview Stats */}
      {overviewStats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Quotas</CardTitle>
              <span className="text-2xl">📊</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overviewStats.total_quotas}</div>
              <p className="text-xs text-gray-500">
                Across {overviewStats.departments_with_quotas} departments
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Exceeded Quotas</CardTitle>
              <span className="text-2xl">🚨</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{overviewStats.quotas_exceeded}</div>
              <p className="text-xs text-gray-500">
                Require immediate attention
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Warning Quotas</CardTitle>
              <span className="text-2xl">⚠️</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{overviewStats.quotas_at_warning}</div>
              <p className="text-xs text-gray-500">
                Above 80% usage threshold
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Usage</CardTitle>
              <span className="text-2xl">📈</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overviewStats.average_usage_percentage.toFixed(1)}%</div>
              <p className="text-xs text-gray-500">
                Across all quotas
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create/Edit Form */}
      {showForm && (
        <QuotaForm
          mode={editingQuota ? 'edit' : 'create'}
          initialData={editingQuota || undefined}
          onSubmit={handleSubmitForm}
          onCancel={handleCancelForm}
          loading={formLoading}
          departments={departments}
          llmConfigurations={llmConfigurations}
          templates={templates}
        />
      )}

      {/* Quotas List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Department Quotas ({quotas.length})</CardTitle>
              <CardDescription>
                Manage usage limits and enforcement policies
              </CardDescription>
            </div>
            
            {/* Filters */}
            <div className="flex gap-2">
              <Button
                variant={filters.exceeded_only ? "default" : "outline"}
                size="sm"
                onClick={() => setFilters({ ...filters, exceeded_only: !filters.exceeded_only, warning_only: false })}
              >
                Exceeded Only
              </Button>
              <Button
                variant={filters.warning_only ? "default" : "outline"}
                size="sm"
                onClick={() => setFilters({ ...filters, warning_only: !filters.warning_only, exceeded_only: false })}
              >
                Warning Only
              </Button>
              {(filters.exceeded_only || filters.warning_only) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setFilters({ exceeded_only: false, warning_only: false })}
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {quotas.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {(filters.exceeded_only || filters.warning_only) 
                ? 'No quotas match the current filters.' 
                : 'No quotas found. Create your first quota to get started.'
              }
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-6 gap-4 font-medium text-sm text-gray-500 border-b pb-2">
                <div>Department</div>
                <div>LLM Model</div>
                <div>Monthly Usage</div>
                <div>Status</div>
                <div>Last Reset</div>
                <div>Actions</div>
              </div>

              {/* Table Rows */}
              {quotas.map((quota) => (
                <div 
                  key={quota.id} 
                  className="grid grid-cols-6 gap-4 items-center py-3 border-b last:border-b-0"
                >
                  <div>
                    <div className="font-medium">{quota.department_name}</div>
                  </div>
                  
                  <div>
                    <div className="font-medium">{quota.llm_model_name}</div>
                    <div className="text-sm text-gray-500">{quota.llm_provider}</div>
                  </div>
                  
                  <div className="text-sm">
                    <div>{formatNumber(quota.current_usage_tokens)} / {formatNumber(quota.monthly_limit_tokens)}</div>
                    <div className="text-xs text-gray-500">
                      {quota.monthly_limit_tokens === 0 ? 'Unlimited' : `${quota.monthly_usage_percentage.toFixed(1)}%`}
                    </div>
                  </div>
                  
                  <div>
                    <Badge 
                      variant={getUsageBadgeVariant(quota.monthly_usage_percentage, quota.is_quota_exceeded)}
                    >
                      {quota.is_quota_exceeded ? 'EXCEEDED' : 
                       quota.is_warning_threshold_reached ? 'WARNING' : 'OK'}
                    </Badge>
                  </div>
                  
                  <div className="text-sm text-gray-500">
                    {formatDate(quota.last_reset)}
                  </div>
                  
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditQuota(quota)}
                      disabled={showForm}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteQuota(quota)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default QuotaManagement;
