import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { adminService } from '../../services/adminService';
import type { 
  User, 
  UserListResponse, 
  UserFilters, 
  Department, 
  Role 
} from '../../types/admin';

interface UserManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

export function UserManagement({ onError, onSuccess, onClearMessages }: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);

  const pageSize = 20;

  useEffect(() => {
    loadUsers();
    loadDepartments();
    loadRoles();
  }, [currentPage, searchTerm]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      const filters: UserFilters = {
        page: currentPage,
        limit: pageSize,
        search: searchTerm || undefined,
      };

      const response: UserListResponse = await adminService.getUsers(filters);
      setUsers(response.users);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadDepartments = async () => {
    try {
      const response = await adminService.getDepartments();
      setDepartments(response.departments);
    } catch (err) {
      console.error('Failed to load departments:', err);
    }
  };

  const loadRoles = async () => {
    try {
      const response = await adminService.getRoles();
      setRoles(response.roles);
    } catch (err) {
      console.error('Failed to load roles:', err);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadUsers();
  };

  const handleActivateUser = async (userId: string) => {
    try {
      await adminService.activateUser(userId);
      onSuccess('User activated successfully');
      loadUsers();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to activate user');
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    try {
      await adminService.deactivateUser(userId);
      onSuccess('User deactivated successfully');
      loadUsers();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to deactivate user');
    }
  };

  const handleDeleteUser = async (userId: string, username: string) => {
    if (window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      try {
        await adminService.deleteUser(userId);
        onSuccess('User deleted successfully');
        loadUsers();
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Failed to delete user');
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getRoleName = (roleId?: string) => {
    if (!roleId) return 'No role';
    const role = roles.find(r => r.id === roleId);
    return role?.name || 'Unknown role';
  };

  const getDepartmentName = (departmentId?: string) => {
    if (!departmentId) return 'No department';
    const department = departments.find(d => d.id === departmentId);
    return department?.name || 'Unknown department';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">User Management</h2>
          <p className="text-muted-foreground">
            Manage user accounts, roles, and departments
          </p>
        </div>
        <Button disabled>
          Add User (Coming Soon)
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Search Users</CardTitle>
          <CardDescription>
            Search by username or email address
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-4">
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1"
            />
            <Button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSearchTerm('');
                setCurrentPage(1);
                loadUsers();
              }}
            >
              Clear
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users ({total})</CardTitle>
          <CardDescription>
            Page {currentPage} of {totalPages}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading users...</div>
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No users found
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-7 gap-4 font-medium text-sm text-muted-foreground border-b pb-2">
                <div>Username</div>
                <div>Email</div>
                <div>Role</div>
                <div>Department</div>
                <div>Status</div>
                <div>Created</div>
                <div>Actions</div>
              </div>

              {/* Table Rows */}
              {users.map((user) => (
                <div 
                  key={user.id} 
                  className="grid grid-cols-7 gap-4 items-center py-2 border-b last:border-b-0"
                >
                  <div>
                    <div className="font-medium">{user.username}</div>
                    {user.is_superuser && (
                      <span className="text-xs bg-red-100 text-red-800 px-1 rounded">
                        Super
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {user.email}
                  </div>
                  <div className="text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {getRoleName(user.role_id)}
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                      {getDepartmentName(user.department_id)}
                    </span>
                  </div>
                  <div>
                    <span 
                      className={`px-2 py-1 rounded text-xs ${
                        user.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(user.created_at)}
                  </div>
                  <div className="flex gap-2">
                    {user.is_active ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeactivateUser(user.id)}
                      >
                        Deactivate
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleActivateUser(user.id)}
                      >
                        Activate
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteUser(user.id, user.username)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-muted-foreground">
                Showing {users.length} of {total} users
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage(currentPage - 1)}
                >
                  Previous
                </Button>
                <span className="px-3 py-1 text-sm">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
