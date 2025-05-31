import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Checkbox } from '../ui/checkbox';
import { adminService } from '../../services/adminService';
import type { 
  Role, 
  RoleCreate, 
  RoleUpdate, 
  RoleListResponse,
  PermissionInfo,
  AvailablePermissionsResponse
} from '../../types/admin';

interface RoleManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

interface RoleFormData {
  name: string;
  description: string;
  permissions: string[];
}

export function RoleManagement({ onError, onSuccess, onClearMessages }: RoleManagementProps) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [availablePermissions, setAvailablePermissions] = useState<PermissionInfo[]>([]);
  const [permissionCategories, setPermissionCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [formData, setFormData] = useState<RoleFormData>({
    name: '',
    description: '',
    permissions: []
  });
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadRoles();
    loadAvailablePermissions();
  }, []);

  const loadRoles = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      const response: RoleListResponse = await adminService.getRoles();
      setRoles(response.roles);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load roles');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailablePermissions = async () => {
    try {
      const response: AvailablePermissionsResponse = await adminService.getAvailablePermissions();
      setAvailablePermissions(response.permissions);
      setPermissionCategories(response.categories);
    } catch (err) {
      console.error('Failed to load permissions:', err);
    }
  };

  const handleCreateRole = () => {
    setEditingRole(null);
    setFormData({ name: '', description: '', permissions: [] });
    setShowForm(true);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    setFormData({
      name: role.name,
      description: role.description || '',
      permissions: [...role.permissions]
    });
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingRole(null);
    setFormData({ name: '', description: '', permissions: [] });
  };

  const handlePermissionChange = (permissionName: string, checked: boolean) => {
    if (checked) {
      setFormData(prev => ({
        ...prev,
        permissions: [...prev.permissions, permissionName]
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        permissions: prev.permissions.filter(p => p !== permissionName)
      }));
    }
  };

  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      onError('Role name is required');
      return;
    }

    if (formData.permissions.length === 0) {
      onError('At least one permission must be selected');
      return;
    }

    try {
      setFormLoading(true);
      onClearMessages();

      if (editingRole) {
        // Update existing role
        const updateData: RoleUpdate = {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined,
          permissions: formData.permissions
        };
        await adminService.updateRole(editingRole.id, updateData);
        onSuccess('Role updated successfully');
      } else {
        // Create new role
        const createData: RoleCreate = {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined,
          permissions: formData.permissions
        };
        await adminService.createRole(createData);
        onSuccess('Role created successfully');
      }

      handleCancelForm();
      loadRoles();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to save role');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteRole = async (role: Role) => {
    if (role.user_count > 0) {
      onError(`Cannot delete role "${role.name}" because it has ${role.user_count} users assigned.`);
      return;
    }

    if (role.name === 'admin') {
      onError('Cannot delete the admin role');
      return;
    }

    if (window.confirm(`Are you sure you want to delete role "${role.name}"? This action cannot be undone.`)) {
      try {
        await adminService.deleteRole(role.id);
        onSuccess('Role deleted successfully');
        loadRoles();
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Failed to delete role');
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getPermissionsByCategory = (category: string) => {
    return availablePermissions.filter(p => p.category === category);
  };

  const formatPermissions = (permissions: string[]) => {
    if (permissions.includes('*')) {
      return 'All permissions (Admin)';
    }
    return permissions.slice(0, 3).join(', ') + (permissions.length > 3 ? ` +${permissions.length - 3} more` : '');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Role Management</h2>
          <p className="text-muted-foreground">
            Manage user roles and permissions
          </p>
        </div>
        <Button onClick={handleCreateRole} disabled={showForm}>
          Add Role
        </Button>
      </div>

      {/* Create/Edit Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingRole ? 'Edit Role' : 'Create New Role'}
            </CardTitle>
            <CardDescription>
              {editingRole 
                ? 'Update role information and permissions' 
                : 'Add a new role with specific permissions'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitForm} className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Role Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter role name"
                    required
                    disabled={formLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Enter role description (optional)"
                    disabled={formLoading}
                  />
                </div>
              </div>

              {/* Permissions */}
              <div className="space-y-4">
                <Label>Permissions *</Label>
                <p className="text-sm text-muted-foreground">
                  Select the permissions this role should have. Users with this role will have access to all selected features.
                </p>
                
                <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
                  {permissionCategories.map(category => (
                    <div key={category} className="mb-6 last:mb-0">
                      <h4 className="font-medium text-sm mb-3 capitalize text-muted-foreground">
                        {category} Permissions
                      </h4>
                      <div className="grid gap-3 md:grid-cols-2">
                        {getPermissionsByCategory(category).map(permission => (
                          <div key={permission.name} className="flex items-start space-x-3">
                            <Checkbox
                              id={permission.name}
                              checked={formData.permissions.includes(permission.name)}
                              onCheckedChange={(checked) => 
                                handlePermissionChange(permission.name, checked as boolean)
                              }
                              disabled={formLoading}
                            />
                            <div className="grid gap-1.5 leading-none">
                              <Label
                                htmlFor={permission.name}
                                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                              >
                                {permission.name}
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                {permission.description}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                {formData.permissions.length === 0 && (
                  <p className="text-sm text-red-600">
                    At least one permission must be selected
                  </p>
                )}
              </div>
              
              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  disabled={formLoading || !formData.name.trim() || formData.permissions.length === 0}
                >
                  {formLoading ? 'Saving...' : (editingRole ? 'Update Role' : 'Create Role')}
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

      {/* Roles List */}
      <Card>
        <CardHeader>
          <CardTitle>Roles ({roles.length})</CardTitle>
          <CardDescription>
            All user roles and their permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading roles...</div>
            </div>
          ) : roles.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No roles found. Create your first role to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-6 gap-4 font-medium text-sm text-muted-foreground border-b pb-2">
                <div>Name</div>
                <div>Description</div>
                <div>Permissions</div>
                <div>Users</div>
                <div>Created</div>
                <div>Actions</div>
              </div>

              {/* Table Rows */}
              {roles.map((role) => (
                <div 
                  key={role.id} 
                  className="grid grid-cols-6 gap-4 items-center py-2 border-b last:border-b-0"
                >
                  <div>
                    <div className="font-medium">{role.name}</div>
                    {role.is_admin_role && (
                      <span className="text-xs bg-red-100 text-red-800 px-1 rounded">
                        Admin
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {role.description || 'No description'}
                  </div>
                  <div className="text-sm">
                    <span className="text-xs text-muted-foreground">
                      {formatPermissions(role.permissions)}
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {role.user_count} users
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(role.created_at)}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditRole(role)}
                      disabled={showForm}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteRole(role)}
                      disabled={role.user_count > 0 || role.name === 'admin'}
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

      {/* Role Summary */}
      {roles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Role Summary</CardTitle>
            <CardDescription>
              Overview of roles and user assignments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <div className="text-sm font-medium">Total Roles</div>
                <div className="text-2xl font-bold">{roles.length}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Total Users with Roles</div>
                <div className="text-2xl font-bold">
                  {roles.reduce((sum, role) => sum + role.user_count, 0)}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Admin Roles</div>
                <div className="text-2xl font-bold text-red-600">
                  {roles.filter(role => role.is_admin_role).length}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
