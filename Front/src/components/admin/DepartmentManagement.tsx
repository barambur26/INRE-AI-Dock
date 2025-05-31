import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { adminService } from '../../services/adminService';
import type { 
  Department, 
  DepartmentCreate, 
  DepartmentUpdate, 
  DepartmentListResponse 
} from '../../types/admin';

interface DepartmentManagementProps {
  onError: (error: string) => void;
  onSuccess: (message: string) => void;
  onClearMessages: () => void;
}

interface DepartmentFormData {
  name: string;
  description: string;
}

export function DepartmentManagement({ onError, onSuccess, onClearMessages }: DepartmentManagementProps) {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [formData, setFormData] = useState<DepartmentFormData>({
    name: '',
    description: ''
  });
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    loadDepartments();
  }, []);

  const loadDepartments = async () => {
    try {
      setLoading(true);
      onClearMessages();
      
      const response: DepartmentListResponse = await adminService.getDepartments();
      setDepartments(response.departments);
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDepartment = () => {
    setEditingDepartment(null);
    setFormData({ name: '', description: '' });
    setShowForm(true);
  };

  const handleEditDepartment = (department: Department) => {
    setEditingDepartment(department);
    setFormData({
      name: department.name,
      description: department.description || ''
    });
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingDepartment(null);
    setFormData({ name: '', description: '' });
  };

  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      onError('Department name is required');
      return;
    }

    try {
      setFormLoading(true);
      onClearMessages();

      if (editingDepartment) {
        // Update existing department
        const updateData: DepartmentUpdate = {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined
        };
        await adminService.updateDepartment(editingDepartment.id, updateData);
        onSuccess('Department updated successfully');
      } else {
        // Create new department
        const createData: DepartmentCreate = {
          name: formData.name.trim(),
          description: formData.description.trim() || undefined
        };
        await adminService.createDepartment(createData);
        onSuccess('Department created successfully');
      }

      handleCancelForm();
      loadDepartments();
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to save department');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteDepartment = async (department: Department) => {
    if (department.user_count > 0) {
      onError(`Cannot delete department "${department.name}" because it has ${department.user_count} users assigned.`);
      return;
    }

    if (window.confirm(`Are you sure you want to delete department "${department.name}"? This action cannot be undone.`)) {
      try {
        await adminService.deleteDepartment(department.id);
        onSuccess('Department deleted successfully');
        loadDepartments();
      } catch (err) {
        onError(err instanceof Error ? err.message : 'Failed to delete department');
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Department Management</h2>
          <p className="text-muted-foreground">
            Manage organizational departments and user assignments
          </p>
        </div>
        <Button onClick={handleCreateDepartment} disabled={showForm}>
          Add Department
        </Button>
      </div>

      {/* Create/Edit Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingDepartment ? 'Edit Department' : 'Create New Department'}
            </CardTitle>
            <CardDescription>
              {editingDepartment 
                ? 'Update department information' 
                : 'Add a new department to the organization'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmitForm} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="name">Department Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter department name"
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
                    placeholder="Enter department description (optional)"
                    disabled={formLoading}
                  />
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  disabled={formLoading || !formData.name.trim()}
                >
                  {formLoading ? 'Saving...' : (editingDepartment ? 'Update Department' : 'Create Department')}
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

      {/* Departments List */}
      <Card>
        <CardHeader>
          <CardTitle>Departments ({departments.length})</CardTitle>
          <CardDescription>
            All organizational departments
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-muted-foreground">Loading departments...</div>
            </div>
          ) : departments.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No departments found. Create your first department to get started.
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-6 gap-4 font-medium text-sm text-muted-foreground border-b pb-2">
                <div>Name</div>
                <div>Description</div>
                <div>Total Users</div>
                <div>Active Users</div>
                <div>Created</div>
                <div>Actions</div>
              </div>

              {/* Table Rows */}
              {departments.map((department) => (
                <div 
                  key={department.id} 
                  className="grid grid-cols-6 gap-4 items-center py-2 border-b last:border-b-0"
                >
                  <div>
                    <div className="font-medium">{department.name}</div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {department.description || 'No description'}
                  </div>
                  <div className="text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                      {department.user_count} users
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                      {department.active_user_count} active
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(department.created_at)}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEditDepartment(department)}
                      disabled={showForm}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => handleDeleteDepartment(department)}
                      disabled={department.user_count > 0}
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

      {/* Department Usage Summary */}
      {departments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Department Summary</CardTitle>
            <CardDescription>
              Overview of user distribution across departments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <div className="text-sm font-medium">Total Departments</div>
                <div className="text-2xl font-bold">{departments.length}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Total Users Assigned</div>
                <div className="text-2xl font-bold">
                  {departments.reduce((sum, dept) => sum + dept.user_count, 0)}
                </div>
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium">Active Users</div>
                <div className="text-2xl font-bold text-green-600">
                  {departments.reduce((sum, dept) => sum + dept.active_user_count, 0)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
