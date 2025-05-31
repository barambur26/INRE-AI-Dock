import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, useLogout } from '../hooks/useAuth';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { LogOut, User, Building, Shield, Activity, Settings } from 'lucide-react';

export default function Dashboard() {
  const { user, isLoading } = useAuth();
  const { logout, isLoading: isLoggingOut } = useLogout();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isAdmin = user?.is_superuser || user?.role_name === 'admin' || user?.role === 'admin';

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">AI Dock App</h1>
              <p className="text-sm text-gray-500">LLM Access Portal</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                Welcome, <span className="font-medium">{user?.username}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                ) : (
                  <>
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">
            Manage your AI LLM access and view your account information
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* User Info Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                User Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-sm font-medium">Username:</span>
                <span className="text-sm text-gray-600 ml-2">{user?.username}</span>
              </div>
              <div>
                <span className="text-sm font-medium">Email:</span>
                <span className="text-sm text-gray-600 ml-2">{user?.email}</span>
              </div>
              <div>
                <span className="text-sm font-medium">Status:</span>
                <span className={`text-sm ml-2 ${user?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                  {user?.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Role & Department Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building className="h-5 w-5" />
                Role & Department
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-sm font-medium">Role:</span>
                <span className="text-sm text-gray-600 ml-2 capitalize">{user?.role_name || user?.role}</span>
              </div>
              <div>
                <span className="text-sm font-medium">Department:</span>
                <span className="text-sm text-gray-600 ml-2">{user?.department_name || user?.department}</span>
              </div>
              <div className="pt-2">
                <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                  isAdmin
                    ? 'bg-purple-100 text-purple-800' 
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  <Shield className="h-3 w-3 mr-1" />
                  {isAdmin ? 'Administrator' : 'Standard User'}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Access Status Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Access Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">LLM Access:</span>
                <span className="text-sm text-green-600">Enabled</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Quota Status:</span>
                <span className="text-sm text-blue-600">Available</span>
              </div>
              <div className="pt-2">
                <div className="text-xs text-gray-500">
                  Ready to interact with configured LLM models
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and navigation shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Button 
                variant="outline" 
                className="justify-start h-auto p-4"
                onClick={() => navigate('/chat')}
              >
                <div className="text-left">
                  <div className="font-medium">Chat Interface</div>
                  <div className="text-sm text-gray-500">Start LLM conversation</div>
                </div>
              </Button>
              
              {isAdmin && (
                <Button 
                  variant="outline" 
                  className="justify-start h-auto p-4"
                  onClick={() => navigate('/admin')}
                >
                  <div className="text-left">
                    <div className="font-medium flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Admin Settings
                    </div>
                    <div className="text-sm text-gray-500">Manage users & departments</div>
                  </div>
                </Button>
              )}
              
              <Button variant="outline" className="justify-start h-auto p-4">
                <div className="text-left">
                  <div className="font-medium">Usage History</div>
                  <div className="text-sm text-gray-500">View past interactions</div>
                </div>
              </Button>
              
              <Button variant="outline" className="justify-start h-auto p-4">
                <div className="text-left">
                  <div className="font-medium">Profile Settings</div>
                  <div className="text-sm text-gray-500">Update preferences</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Development Notice */}
        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <Activity className="h-5 w-5 text-yellow-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Development Status
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  This is the main dashboard. Additional features like chat interface, 
                  admin settings, and LLM configuration will be implemented in subsequent tasks.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
