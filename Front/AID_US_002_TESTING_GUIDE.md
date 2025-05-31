# AID-US-002 Testing Guide: Admin Interface for User & Department Management

## 🎯 **Feature Overview**
Complete admin interface for managing users, departments, and roles with full CRUD operations and proper admin-only access control.

## 🚀 **Quick Start Testing**

### **Prerequisites**
1. ✅ Backend server running on `http://localhost:8000`
2. ✅ Frontend server running on `http://localhost:8080`
3. ✅ Admin user account available for testing

### **Test Credentials (from AID-US-001C)**
- **Admin User:** `admin` / `admin123`
- **Regular User:** `user1` / `password123`

---

## 📋 **Test Scenarios**

### **🔐 Test 1: Admin Access Control**

**Objective:** Verify only admin users can access the admin interface

**Steps:**
1. **Login as regular user:**
   ```
   Username: user1
   Password: password123
   ```
2. Navigate to `http://localhost:8080/dashboard`
3. ✅ **Expected:** No "Admin Settings" button visible
4. Try to access `http://localhost:8080/admin` directly
5. ✅ **Expected:** Redirected back to dashboard

6. **Login as admin user:**
   ```
   Username: admin
   Password: admin123
   ```
7. Navigate to `http://localhost:8080/dashboard`
8. ✅ **Expected:** "Admin Settings" button visible in Quick Actions
9. Click "Admin Settings" button
10. ✅ **Expected:** Successfully navigate to admin interface

---

### **👥 Test 2: User Management**

**Objective:** Test complete user CRUD operations

**Steps:**

**A. View Users**
1. Go to Admin → Users tab
2. ✅ **Expected:** See paginated list of users
3. ✅ **Expected:** See search functionality
4. ✅ **Expected:** See user details (username, email, role, department, status)

**B. Search Users**
1. Enter "admin" in search box and click Search
2. ✅ **Expected:** Filter results to show admin user
3. Click "Clear" button
4. ✅ **Expected:** Return to full user list

**C. User Actions**
1. Find an active user (not yourself)
2. Click "Deactivate" button
3. ✅ **Expected:** User status changes to "Inactive"
4. Click "Activate" button
5. ✅ **Expected:** User status changes back to "Active"

**D. Delete User (if safe test user available)**
1. Try to delete a user with no critical data
2. ✅ **Expected:** Confirmation dialog appears
3. ✅ **Expected:** User deleted successfully or proper error message

---

### **🏢 Test 3: Department Management**

**Objective:** Test department CRUD operations

**Steps:**

**A. View Departments**
1. Go to Admin → Departments tab
2. ✅ **Expected:** See list of departments with user counts

**B. Create Department**
1. Click "Add Department" button
2. ✅ **Expected:** Form appears
3. Fill in:
   - Name: "Test Department"
   - Description: "Department for testing purposes"
4. Click "Create Department"
5. ✅ **Expected:** Success message and department appears in list

**C. Edit Department**
1. Find the "Test Department" and click "Edit"
2. ✅ **Expected:** Form pre-populated with department data
3. Change description to "Updated test department"
4. Click "Update Department"
5. ✅ **Expected:** Success message and changes reflected

**D. Delete Department**
1. Click "Delete" on "Test Department"
2. ✅ **Expected:** Confirmation dialog
3. Confirm deletion
4. ✅ **Expected:** Department removed from list
5. Try to delete a department with users
6. ✅ **Expected:** Error message preventing deletion

---

### **🔐 Test 4: Role Management**

**Objective:** Test role and permission management

**Steps:**

**A. View Roles**
1. Go to Admin → Roles tab
2. ✅ **Expected:** See list of roles with permission summaries

**B. View Available Permissions**
1. Click "Add Role" button
2. ✅ **Expected:** Form shows categorized permissions
3. ✅ **Expected:** Permissions grouped by category (system, user, admin, etc.)

**C. Create Role**
1. Fill in:
   - Name: "Test Manager"
   - Description: "Test role for managers"
   - Select permissions: "chat", "view_profile", "view_usage", "view_reports"
2. Click "Create Role"
3. ✅ **Expected:** Success message and role appears in list

**D. Edit Role**
1. Find "Test Manager" role and click "Edit"
2. Add "manage_department_users" permission
3. Click "Update Role"
4. ✅ **Expected:** Role updated successfully

**E. Delete Role**
1. Click "Delete" on "Test Manager" role
2. ✅ **Expected:** Role deleted (if no users assigned)

---

### **📊 Test 5: Admin Statistics**

**Objective:** Verify dashboard statistics are accurate

**Steps:**

1. Go to Admin → Overview tab
2. ✅ **Expected:** See statistics cards with:
   - Total Users count
   - Active Users count
   - Total Departments count
   - Total Roles count
   - Recent Users count (last 30 days)

3. ✅ **Expected:** See "Users by Role" chart with correct data
4. ✅ **Expected:** See "Users by Department" chart with correct data
5. Click "Refresh" button
6. ✅ **Expected:** Statistics update

---

### **🚀 Test 6: Initialize Default Data**

**Objective:** Test system initialization

**Steps:**

1. Go to Admin → Overview tab
2. Click "Initialize Default Data" button
3. ✅ **Expected:** Success message
4. Go to Departments tab
5. ✅ **Expected:** See default departments (General, IT, Finance, HR, Marketing, Operations)
6. Go to Roles tab
7. ✅ **Expected:** See default roles (admin, user, analyst, manager)

---

## 🐛 **Error Handling Tests**

### **Test 7: Form Validation**

**A. User Form Validation**
1. Try creating user with:
   - Empty username → ✅ **Expected:** Validation error
   - Invalid email → ✅ **Expected:** Validation error
   - Weak password → ✅ **Expected:** Validation error
   - Duplicate username → ✅ **Expected:** Server error with proper message

**B. Department Form Validation**
1. Try creating department with:
   - Empty name → ✅ **Expected:** Validation error
   - Duplicate name → ✅ **Expected:** Server error with proper message

**C. Role Form Validation**
1. Try creating role with:
   - Empty name → ✅ **Expected:** Validation error
   - No permissions selected → ✅ **Expected:** Validation error

### **Test 8: Permission Checks**
1. Verify non-admin users cannot access `/admin` routes
2. Verify API calls include proper authentication headers
3. Verify proper error messages for unauthorized actions

---

## 🔧 **Backend API Testing**

### **Direct API Testing (Optional)**

You can test the backend APIs directly using curl or a tool like Postman:

**1. Get Admin Token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'
```

**2. Test Admin Health:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/health" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

**3. Get Admin Stats:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

**4. List Users:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/" \
     -H "Authorization: Bearer YOUR_TOKEN"
```

---

## ✅ **Success Criteria**

### **Functional Requirements:**
- ✅ Admin-only access to admin interface
- ✅ Complete user CRUD operations
- ✅ Complete department CRUD operations  
- ✅ Complete role CRUD operations
- ✅ Proper form validation and error handling
- ✅ Real-time statistics and data refresh
- ✅ Responsive UI design

### **Security Requirements:**
- ✅ Non-admin users cannot access admin features
- ✅ Proper authentication token handling
- ✅ Secure API endpoints with authorization
- ✅ Prevention of dangerous operations (deleting last admin, etc.)

### **User Experience Requirements:**
- ✅ Intuitive navigation and interface
- ✅ Clear success and error messages
- ✅ Loading states and proper feedback
- ✅ Consistent design with existing app

---

## 🚨 **Troubleshooting**

### **Common Issues:**

**1. Cannot access admin interface**
- Check if user has admin role or is_superuser = true
- Verify backend authentication is working
- Check browser console for errors

**2. API calls failing**
- Verify backend server is running on port 8000
- Check if authentication token is valid
- Verify CORS settings

**3. Data not updating**
- Check backend logs for errors
- Verify database connection
- Try refreshing the page

**4. Form validation errors**
- Check required fields are filled
- Verify password meets strength requirements
- Ensure unique constraints (username, email, department/role names)

---

## 📝 **Test Results Documentation**

When testing, document results as follows:

```
✅ PASS - Feature works as expected
❌ FAIL - Feature has issues (describe the issue)
⚠️  PARTIAL - Feature works but has minor issues
```

**Example:**
- ✅ PASS - User creation works correctly
- ❌ FAIL - Department deletion shows error even when department has no users  
- ⚠️  PARTIAL - Role editing works but permissions don't update immediately

---

## 🎉 **Completion Checklist**

- [ ] All admin access controls working
- [ ] User management CRUD complete
- [ ] Department management CRUD complete
- [ ] Role management CRUD complete
- [ ] Statistics dashboard functional
- [ ] Form validation working
- [ ] Error handling proper
- [ ] Navigation and routing correct
- [ ] Admin-only restrictions enforced
- [ ] Integration between frontend and backend successful

---

**🚀 Ready to test! Start with Test 1 and work through each scenario systematically.**
