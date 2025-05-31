import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import type { AdminStats as AdminStatsType } from '../../types/admin';

interface AdminStatsProps {
  stats: AdminStatsType;
  loading: boolean;
  onRefresh: () => void;
}

export function AdminStats({ stats, loading, onRefresh }: AdminStatsProps) {
  const formatPercentage = (value: number, total: number): string => {
    if (total === 0) return '0%';
    return `${Math.round((value / total) * 100)}%`;
  };

  const getTopItems = (data: Record<string, number>, limit: number = 3) => {
    return Object.entries(data)
      .sort(([, a], [, b]) => b - a)
      .slice(0, limit);
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <span className="text-2xl">👥</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_users}</div>
            <p className="text-xs text-muted-foreground">
              {stats.active_users} active ({formatPercentage(stats.active_users, stats.total_users)})
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Departments</CardTitle>
            <span className="text-2xl">🏢</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_departments}</div>
            <p className="text-xs text-muted-foreground">
              Organizational units
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Roles</CardTitle>
            <span className="text-2xl">🔐</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_roles}</div>
            <p className="text-xs text-muted-foreground">
              Permission groups
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">New Users</CardTitle>
            <span className="text-2xl">📈</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.recent_users_count}</div>
            <p className="text-xs text-muted-foreground">
              Last 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Users by Role */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Users by Role</CardTitle>
              <CardDescription>Distribution of users across roles</CardDescription>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onRefresh}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {getTopItems(stats.users_by_role).map(([role, count]) => (
                <div key={role} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium capitalize">{role}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-muted-foreground">
                      {count} users
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({formatPercentage(count, stats.total_users)})
                    </span>
                  </div>
                </div>
              ))}
              
              {Object.keys(stats.users_by_role).length === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  No role data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Users by Department */}
        <Card>
          <CardHeader>
            <CardTitle>Users by Department</CardTitle>
            <CardDescription>Distribution of users across departments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {getTopItems(stats.users_by_department).map(([department, count]) => (
                <div key={department} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium">{department}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-muted-foreground">
                      {count} users
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({formatPercentage(count, stats.total_users)})
                    </span>
                  </div>
                </div>
              ))}
              
              {Object.keys(stats.users_by_department).length === 0 && (
                <div className="text-center py-4 text-muted-foreground">
                  No department data available
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Overall system status and key metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <div className="text-sm font-medium">User Activity</div>
              <div className="text-2xl font-bold text-green-600">
                {formatPercentage(stats.active_users, stats.total_users)}
              </div>
              <div className="text-xs text-muted-foreground">
                {stats.active_users} of {stats.total_users} users active
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium">Role Coverage</div>
              <div className="text-2xl font-bold text-blue-600">
                {Object.keys(stats.users_by_role).length}
              </div>
              <div className="text-xs text-muted-foreground">
                Roles in use
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium">Department Coverage</div>
              <div className="text-2xl font-bold text-purple-600">
                {Object.keys(stats.users_by_department).length}
              </div>
              <div className="text-xs text-muted-foreground">
                Departments with users
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
