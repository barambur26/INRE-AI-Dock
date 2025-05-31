import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { useAuth } from '../hooks/useAuth';
import { UserManagement } from '../components/admin/UserManagement';
import { DepartmentManagement } from '../components/admin/DepartmentManagement';
import { RoleManagement } from '../components/admin/RoleManagement';
import { LLMConfigurationManagement } from '../components/admin/LLMConfigurationManagement';
import { QuotaManagement } from '../components/admin/QuotaManagement';
import { UsageMonitoring } from '../components/admin/UsageMonitoring';
import { AdminStats } from '../components/admin/AdminStats';
import { adminService } from '../services/adminService';
import type { AdminStats as AdminStatsType } from '../types/admin';

type AdminTab = 'overview' | 'users' | 'departments' | 'roles' | 'llm-config' | 'quotas' | 'usage-monitoring' | 'settings';

interface TabConfig {
  id: AdminTab;
  label: string;
  icon: string;
  description: string;
}

const tabs: TabConfig[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: '📊',
    description: 'Admin dashboard and statistics'
  },
  {
    id: 'users',
    label: 'Users',
    icon: '👥',
    description: 'Manage users and their access'
  },
  {
    id: 'departments',
    label: 'Departments',
    icon: '🏢',
    description: 'Manage organizational departments'
  },
  {
    id: 'roles',
    label: 'Roles',
    icon: '🔐',
    description: 'Manage roles and permissions'
  },
  {
    id: 'llm-config',
    label: 'LLM Config',
    icon: '🤖',
    description: 'Configure available LLM models'
  },
  {
    id: 'quotas',
    label: 'Quotas',
    icon: '⚖️',
    description: 'Manage department usage quotas'
  },
  {
    id: 'usage-monitoring',
    label: 'Usage Monitor',
    icon: '📈',
    description: 'Real-time usage monitoring and analytics'
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    description: 'System configuration and settings'
  }
];

export function AdminSettings() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [stats, setStats] = useState<AdminStatsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check if user has admin privileges
  useEffect(() => {
    if (user && !user.is_admin && user.role_name !== 'admin') {
      setError('You do not have admin privileges to access this page.');
      setTimeout(() => {
        logout();
      }, 3000);
    }
  }, [user, logout]);

  // Load admin statistics
  useEffect(() => {
    if (activeTab === 'overview') {
      loadStats();
    }
  }, [activeTab]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const statsData = await adminService.getAdminStats();
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const initializeDefaultData = async () => {
    try {
      setLoading(true);
      await adminService.initializeDefaultData();
      setSuccess('Default roles and departments created successfully');
      if (activeTab === 'overview') {
        await loadStats();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize default data');
    } finally {
      setLoading(false);
    }
  };

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold tracking-tight">Admin Dashboard</h2>
                <p className="text-muted-foreground">
                  Overview of system statistics and quick actions
                </p>
              </div>
              <Button 
                onClick={initializeDefaultData}
                disabled={loading}
                variant="outline"
              >
                Initialize Default Data
              </Button>
            </div>
            
            {stats ? (
              <AdminStats stats={stats} loading={loading} onRefresh={loadStats} />
            ) : (
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
            )}
          </div>
        );
      
      case 'users':
        return (
          <UserManagement 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'departments':
        return (
          <DepartmentManagement 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'roles':
        return (
          <RoleManagement 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'llm-config':
        return (
          <LLMConfigurationManagement 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'quotas':
        return (
          <QuotaManagement 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'usage-monitoring':
        return (
          <UsageMonitoring 
            onError={setError}
            onSuccess={setSuccess}
            onClearMessages={clearMessages}
          />
        );
      
      case 'settings':
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold tracking-tight">System Settings</h2>
              <p className="text-muted-foreground">
                Configure system-wide settings and preferences
              </p>
            </div>
            
            <Card>
              <CardHeader>
                <CardTitle>System Information</CardTitle>
                <CardDescription>
                  Current system status and configuration
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <strong>Current User:</strong> {user?.username} ({user?.email})
                  </div>
                  <div>
                    <strong>Role:</strong> {user?.role_name || 'No role assigned'}
                  </div>
                  <div>
                    <strong>Department:</strong> {user?.department_name || 'No department assigned'}
                  </div>
                  <div>
                    <strong>Superuser:</strong> {user?.is_superuser ? 'Yes' : 'No'}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        );
      
      default:
        return <div>Tab content not implemented yet</div>;
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-muted-foreground">Please log in to access the admin panel.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">AI Dock Admin</h1>
              <p className="text-muted-foreground">
                Welcome back, {user.username}
              </p>
            </div>
            <Button 
              onClick={logout}
              variant="outline"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="container mx-auto px-4 py-2">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{error}</span>
            <button
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={clearMessages}
            >
              <span className="sr-only">Dismiss</span>
              ✕
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="container mx-auto px-4 py-2">
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded relative">
            <span className="block sm:inline">{success}</span>
            <button
              className="absolute top-0 bottom-0 right-0 px-4 py-3"
              onClick={clearMessages}
            >
              <span className="sr-only">Dismiss</span>
              ✕
            </button>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Sidebar Navigation */}
          <div className="w-64 shrink-0">
            <Card>
              <CardContent className="p-2">
                <nav className="space-y-1">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                        activeTab === tab.id
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                      }`}
                    >
                      <span className="mr-3 text-base">{tab.icon}</span>
                      <div className="text-left">
                        <div>{tab.label}</div>
                        <div className="text-xs opacity-75">{tab.description}</div>
                      </div>
                    </button>
                  ))}
                </nav>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AdminSettings;