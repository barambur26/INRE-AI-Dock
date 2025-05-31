import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { adminService } from '../../services/adminService';

interface LLMConfigurationManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

interface LLMConfiguration {
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

interface LLMConfigFormData {
  model_name: string;
  provider: string;
  display_name: string;
  base_url: string;
  enabled: boolean;
  api_key_env_var: string;
  config_json: string; // JSON string for editing
}

interface ValidationResult {
  is_valid: boolean;
  issues: Array<{
    level: string;
    message: string;
    field?: string;
    suggestion?: string;
  }>;
}

export function LLMConfigurationManagement({ onError, onSuccess, onClearMessages }: LLMConfigurationManagementProps) {
  const [configurations, setConfigurations] = useState<LLMConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [showJsonImport, setShowJsonImport] = useState(false);
  const [editingConfig, setEditingConfig] = useState<LLMConfiguration | null>(null);
  const [formData, setFormData] = useState<LLMConfigFormData>({
    model_name: '',
    provider: '',
    display_name: '',
    base_url: '',
    enabled: true,
    api_key_env_var: '',
    config_json: '{}' // Default empty JSON
  });
  const [formLoading, setFormLoading] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [jsonValidationResult, setJsonValidationResult] = useState<any>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    loadConfigurations();
    loadProviders();
    loadStats();
  }, []);

  const loadConfigurations = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      // Mock service call - replace with real API call when backend is connected
      const mockConfigurations: LLMConfiguration[] = [
        {
          id: '1',
          model_name: 'gpt-4',
          provider: 'openai',
          display_name: 'GPT-4',
          base_url: 'https://api.openai.com/v1',
          enabled: true,
          config_json: { max_tokens: 2000, temperature: 0.7 },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          quota_count: 3,
          usage_count: 150
        },
        {
          id: '2',
          model_name: 'claude-3-sonnet',
          provider: 'anthropic',
          display_name: 'Claude 3 Sonnet',
          base_url: 'https://api.anthropic.com',
          enabled: false,
          config_json: { max_tokens: 2000, temperature: 0.7 },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          quota_count: 1,
          usage_count: 0
        }
      ];
      
      setConfigurations(mockConfigurations);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load LLM configurations');
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      // Mock providers data
      const mockProviders = [
        {
          name: 'openai',
          display_name: 'OpenAI',
          supported_models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
          default_config: { max_tokens: 2000, temperature: 0.7 },
          required_env_vars: ['OPENAI_API_KEY']
        },
        {
          name: 'anthropic',
          display_name: 'Anthropic',
          supported_models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
          default_config: { max_tokens: 2000, temperature: 0.7 },
          required_env_vars: ['ANTHROPIC_API_KEY']
        }
      ];
      
      setProviders(mockProviders);
    } catch (err) {
      console.error('Failed to load providers:', err);
    }
  };

  const loadStats = async () => {
    try {
      // Mock stats data
      const mockStats = {
        total_configurations: configurations.length,
        enabled_configurations: configurations.filter(c => c.enabled).length,
        disabled_configurations: configurations.filter(c => !c.enabled).length,
        configurations_by_provider: configurations.reduce((acc, config) => {
          acc[config.provider] = (acc[config.provider] || 0) + 1;
          return acc;
        }, {} as Record<string, number>)
      };
      
      setStats(mockStats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleCreateConfiguration = () => {
    setEditingConfig(null);
    setFormData({
      model_name: '',
      provider: '',
      display_name: '',
      base_url: '',
      enabled: true,
      api_key_env_var: '',
      config_json: JSON.stringify({ max_tokens: 2000, temperature: 0.7 }, null, 2)
    });
    setShowForm(true);
  };

  const handleEditConfiguration = (config: LLMConfiguration) => {
    setEditingConfig(config);
    setFormData({
      model_name: config.model_name,
      provider: config.provider,
      display_name: config.display_name || '',
      base_url: config.base_url || '',
      enabled: config.enabled,
      api_key_env_var: '',
      config_json: JSON.stringify(config.config_json, null, 2)
    });
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setShowJsonImport(false);
    setEditingConfig(null);
    setJsonValidationResult(null);
    setFormData({
      model_name: '',
      provider: '',
      display_name: '',
      base_url: '',
      enabled: true,
      api_key_env_var: '',
      config_json: '{}'
    });
  };

  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.model_name.trim() || !formData.provider.trim()) {
      onError('Model name and provider are required');
      return;
    }

    // Validate JSON
    try {
      JSON.parse(formData.config_json);
    } catch (err) {
      onError('Invalid JSON in configuration');
      return;
    }

    try {
      setFormLoading(true);
      onClearMessages();

      // Mock API call - replace with real service call
      if (editingConfig) {
        onSuccess('LLM configuration updated successfully');
      } else {
        onSuccess('LLM configuration created successfully');
      }

      handleCancelForm();
      loadConfigurations();
      loadStats();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to save LLM configuration');
    } finally {
      setFormLoading(false);
    }
  };

  const handleToggleEnabled = async (config: LLMConfiguration) => {
    try {
      // Mock API call - replace with real service call
      const updatedConfigs = configurations.map(c => 
        c.id === config.id ? { ...c, enabled: !c.enabled } : c
      );
      setConfigurations(updatedConfigs);
      
      onSuccess(`Configuration ${!config.enabled ? 'enabled' : 'disabled'} successfully`);
      loadStats();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to toggle configuration');
    }
  };

  const handleDeleteConfiguration = async (config: LLMConfiguration) => {
    if (config.quota_count > 0 || config.usage_count > 0) {
      onError(`Cannot delete configuration "${config.model_name}" because it has ${config.quota_count} quotas and ${config.usage_count} usage logs.`);
      return;
    }

    if (window.confirm(`Are you sure you want to delete configuration "${config.model_name}"? This action cannot be undone.`)) {
      try {
        // Mock API call - replace with real service call
        setConfigurations(configurations.filter(c => c.id !== config.id));
        onSuccess('Configuration deleted successfully');
        loadStats();
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Failed to delete configuration');
      }
    }
  };

  const handleValidateJson = async () => {
    if (!jsonInput.trim()) {
      onError('Please enter JSON configuration to validate');
      return;
    }

    try {
      const parsedJson = JSON.parse(jsonInput);
      
      // Mock validation result
      const mockValidation = {
        overall_valid: true,
        configurations: parsedJson.configurations || [],
        validation_results: (parsedJson.configurations || []).map((config: any, index: number) => ({
          is_valid: true,
          issues: config.model_name ? [] : [{
            level: 'error',
            message: 'Model name is required',
            field: 'model_name'
          }]
        }))
      };
      
      setJsonValidationResult(mockValidation);
      
      if (mockValidation.overall_valid) {
        onSuccess('JSON configuration is valid');
      } else {
        onError('JSON configuration has validation errors');
      }
    } catch (err) {
      onError('Invalid JSON format');
      setJsonValidationResult(null);
    }
  };

  const handleImportJson = async () => {
    if (!jsonValidationResult || !jsonValidationResult.overall_valid) {
      onError('Please validate the JSON configuration first');
      return;
    }

    try {
      setFormLoading(true);
      // Mock import - replace with real service call
      onSuccess(`Successfully imported ${jsonValidationResult.configurations.length} configurations`);
      handleCancelForm();
      loadConfigurations();
      loadStats();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to import configurations');
    } finally {
      setFormLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (enabled: boolean) => (
    <span className={`px-2 py-1 rounded text-xs ${
      enabled 
        ? 'bg-green-100 text-green-800' 
        : 'bg-red-100 text-red-800'
    }`}>
      {enabled ? 'Enabled' : 'Disabled'}
    </span>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">LLM Configuration</h2>
          <p className="text-muted-foreground">
            Configure available Large Language Model providers and settings
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setShowJsonImport(true)} 
            disabled={showForm || showJsonImport}
          >
            Import JSON
          </Button>
          <Button onClick={handleCreateConfiguration} disabled={showForm || showJsonImport}>
            Add Configuration
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{stats.total_configurations}</div>
              <p className="text-xs text-muted-foreground">Total Configurations</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{stats.enabled_configurations}</div>
              <p className="text-xs text-muted-foreground">Enabled</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{stats.disabled_configurations}</div>
              <p className="text-xs text-muted-foreground">Disabled</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold">{Object.keys(stats.configurations_by_provider).length}</div>
              <p className="text-xs text-muted-foreground">Providers</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Create/Edit Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingConfig ? 'Edit LLM Configuration' : 'Create New LLM Configuration'}
            </CardTitle>
            <CardDescription>
              {editingConfig 
                ? 'Update LLM configuration settings' 
                : 'Add a new Large Language Model configuration'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitForm} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="model_name">Model Name *</Label>
                  <Input
                    id="model_name"
                    value={formData.model_name}
                    onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                    placeholder="e.g., gpt-4, claude-3-sonnet"
                    required
                    disabled={formLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="provider">Provider *</Label>
                  <Input
                    id="provider"
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    placeholder="e.g., openai, anthropic"
                    required
                    disabled={formLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="display_name">Display Name</Label>
                  <Input
                    id="display_name"
                    value={formData.display_name}
                    onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                    placeholder="Human-readable name"
                    disabled={formLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="base_url">Base URL</Label>
                  <Input
                    id="base_url"
                    value={formData.base_url}
                    onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                    placeholder="https://api.openai.com/v1"
                    disabled={formLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="api_key_env_var">API Key Environment Variable</Label>
                  <Input
                    id="api_key_env_var"
                    value={formData.api_key_env_var}
                    onChange={(e) => setFormData({ ...formData, api_key_env_var: e.target.value })}
                    placeholder="OPENAI_API_KEY"
                    disabled={formLoading}
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="enabled"
                    checked={formData.enabled}
                    onCheckedChange={(checked) => setFormData({ ...formData, enabled: !!checked })}
                    disabled={formLoading}
                  />
                  <Label htmlFor="enabled">Enable this configuration</Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="config_json">Configuration JSON</Label>
                <textarea
                  id="config_json"
                  value={formData.config_json}
                  onChange={(e) => setFormData({ ...formData, config_json: e.target.value })}
                  placeholder='{"max_tokens": 2000, "temperature": 0.7}'
                  className="w-full h-32 p-3 border rounded-md font-mono text-sm"
                  disabled={formLoading}
                />
                <p className="text-xs text-muted-foreground">
                  Valid JSON object with model-specific configuration parameters
                </p>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  disabled={formLoading || !formData.model_name.trim() || !formData.provider.trim()}
                >
                  {formLoading ? 'Saving...' : (editingConfig ? 'Update Configuration' : 'Create Configuration')}
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handleCancelForm}
                  disabled={formLoading}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* JSON Import Form */}
      {showJsonImport && (
        <Card>
          <CardHeader>
            <CardTitle>Import LLM Configurations from JSON</CardTitle>
            <CardDescription>
              Paste your JSON configuration to validate and import multiple LLM configurations at once
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="json_input">JSON Configuration</Label>
              <textarea
                id="json_input"
                value={jsonInput}
                onChange={(e) => setJsonInput(e.target.value)}
                placeholder={`{
  "configurations": [
    {
      "model_name": "gpt-4",
      "provider": "openai",
      "display_name": "GPT-4",
      "base_url": "https://api.openai.com/v1",
      "enabled": true,
      "api_key_env_var": "OPENAI_API_KEY",
      "config": {
        "max_tokens": 2000,
        "temperature": 0.7
      }
    }
  ]
}`}
                className="w-full h-48 p-3 border rounded-md font-mono text-sm"
                disabled={formLoading}
              />
            </div>

            {jsonValidationResult && (
              <div className="space-y-2">
                <div className={`p-3 rounded-md ${
                  jsonValidationResult.overall_valid 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="font-medium">
                    {jsonValidationResult.overall_valid ? '✅ Valid Configuration' : '❌ Invalid Configuration'}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Found {jsonValidationResult.configurations.length} configurations
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex gap-2">
              <Button 
                type="button" 
                variant="outline"
                onClick={handleValidateJson}
                disabled={formLoading || !jsonInput.trim()}
              >
                Validate JSON
              </Button>
              <Button 
                type="button" 
                onClick={handleImportJson}
                disabled={formLoading || !jsonValidationResult?.overall_valid}
              >
                {formLoading ? 'Importing...' : 'Import Configurations'}
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                onClick={handleCancelForm}
                disabled={formLoading}
              >
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configurations List */}
      <Card>
        <CardHeader>
          <CardTitle>LLM Configurations ({configurations.length})</CardTitle>
          <CardDescription>
            Manage all configured Large Language Models
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading configurations...</div>
            </div>
          ) : configurations.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No LLM configurations found. Create your first configuration to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-8 gap-4 font-medium text-sm text-muted-foreground border-b pb-2">
                <div>Model</div>
                <div>Provider</div>
                <div>Status</div>
                <div>Base URL</div>
                <div>Quotas</div>
                <div>Usage</div>
                <div>Created</div>
                <div>Actions</div>
              </div>

              {/* Table Rows */}
              {configurations.map((config) => (
                <div 
                  key={config.id} 
                  className="grid grid-cols-8 gap-4 items-center py-2 border-b last:border-b-0"
                >
                  <div>
                    <div className="font-medium">{config.model_name}</div>
                    {config.display_name && (
                      <div className="text-xs text-muted-foreground">{config.display_name}</div>
                    )}
                  </div>
                  <div className="text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs capitalize">
                      {config.provider}
                    </span>
                  </div>
                  <div>
                    {getStatusBadge(config.enabled)}
                  </div>
                  <div className="text-sm text-muted-foreground truncate">
                    {config.base_url || 'Default'}
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">{config.quota_count}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">{config.usage_count}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(config.created_at)}
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleToggleEnabled(config)}
                      disabled={showForm || showJsonImport}
                    >
                      {config.enabled ? 'Disable' : 'Enable'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditConfiguration(config)}
                      disabled={showForm || showJsonImport}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteConfiguration(config)}
                      disabled={config.quota_count > 0 || config.usage_count > 0 || showForm || showJsonImport}
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

      {/* Provider Information */}
      {providers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Available Providers</CardTitle>
            <CardDescription>
              Information about supported LLM providers and their default configurations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              {providers.map((provider) => (
                <div key={provider.name} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{provider.display_name}</h4>
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">{provider.name}</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="font-medium">Models:</span> {provider.supported_models.join(', ')}
                    </div>
                    <div>
                      <span className="font-medium">Required ENV:</span> {provider.required_env_vars.join(', ')}
                    </div>
                    <div>
                      <span className="font-medium">Default Config:</span> 
                      <code className="ml-1 text-xs bg-gray-100 px-1 rounded">
                        {JSON.stringify(provider.default_config)}
                      </code>
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
}
