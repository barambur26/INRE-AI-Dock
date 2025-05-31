# AID-US-007 Comprehensive Testing Guide
## Basic Quota Enforcement (Pre-Request Check) - Complete Testing Scenarios

**Feature**: Basic Quota Enforcement (Pre-Request Check)  
**Status**: Phase 4 - Comprehensive Testing  
**Last Updated**: May 31, 2025  
**Components Tested**: Backend quota enforcement, Frontend error handling, Admin monitoring  

---

## Overview

This guide provides comprehensive testing scenarios for the quota enforcement system implemented in AID-US-007. The system includes:

- **Backend**: Pre-request quota validation in `chat_service.py` and `quota_service.py`
- **Frontend**: Error handling and quota status displays in chat interface
- **Admin**: Real-time usage monitoring and quota management dashboard

---

## Prerequisites

### Backend Setup
1. Backend server running at `http://localhost:8000`
2. Database with User, Department, LLMConfiguration, and DepartmentQuota tables
3. At least one enabled LLM configuration
4. Test departments and users with various quota configurations

### Frontend Setup
1. Frontend running at `http://localhost:8080`
2. Authenticated user sessions for different departments
3. Admin user account for testing administrative features

### Test Data Requirements
```bash
# Required test data:
- Department A: Engineering (Quota: 100,000 tokens/month, Currently used: 5,000)
- Department B: Marketing (Quota: 50,000 tokens/month, Currently used: 45,000) 
- Department C: Sales (Quota: 30,000 tokens/month, Currently used: 31,000)
- Department D: Unlimited (Quota: 0 tokens/month - unlimited)

# Test Users:
- john.doe@company.com (Engineering - Admin)
- jane.smith@company.com (Marketing - User)
- mike.johnson@company.com (Sales - User) 
- admin@company.com (Admin across all departments)
```

---

## Phase 1: Backend Quota Enforcement Testing

### Test Group 1: Basic Quota Validation

#### Test 1.1: Normal Usage (Within Limits)
**Scenario**: User from Engineering department (5,000/100,000 tokens used) sends a message  
**Expected Behavior**: Request proceeds successfully

**Steps**:
1. Log in as `john.doe@company.com` (Engineering)
2. Send POST to `/api/v1/chat/send-message`
   ```json
   {
     "message": "Write a short summary about artificial intelligence",
     "conversation_id": null
   }
   ```
3. **Expected Response**: 
   - Status: 200 OK
   - Response contains LLM message
   - Usage log entry created
   - Quota usage incremented

**Validation**:
- [ ] Request succeeds
- [ ] Response contains valid LLM response
- [ ] `UsageLog` table updated with new entry
- [ ] `DepartmentQuota.current_usage_tokens` incremented correctly
- [ ] No error messages in frontend

#### Test 1.2: Warning Threshold (80-100%)
**Scenario**: User from Marketing department (45,000/50,000 tokens used - 90%) sends a message  
**Expected Behavior**: Request proceeds with warning message

**Steps**:
1. Log in as `jane.smith@company.com` (Marketing)
2. Send chat message via frontend interface
3. **Expected Response**:
   - Request succeeds but shows warning banner
   - QuotaStatusIndicator shows "warning" state (yellow)
   - Warning message about approaching quota limit

**Validation**:
- [ ] Request completes successfully
- [ ] Warning banner displayed in chat interface
- [ ] QuotaStatusIndicator shows yellow warning state
- [ ] Warning message mentions "approaching quota limit"
- [ ] Usage tracking continues normally

#### Test 1.3: Quota Exceeded (Hard Limit)
**Scenario**: User from Sales department (31,000/30,000 tokens used - 103%) attempts to send a message  
**Expected Behavior**: Request blocked with quota exceeded error

**Steps**:
1. Log in as `mike.johnson@company.com` (Sales)
2. Attempt to send chat message
3. **Expected Response**:
   - Status: 403 Forbidden (or appropriate quota error)
   - Error message explaining quota exceeded
   - No LLM API call made
   - No usage log entry created

**Validation**:
- [ ] Request blocked before LLM call
- [ ] Error message clearly explains quota exceeded
- [ ] QuotaStatusIndicator shows "exceeded" state (red)
- [ ] "Contact Admin" button appears
- [ ] No tokens deducted from quota
- [ ] No usage log entry created

#### Test 1.4: Unlimited Quota
**Scenario**: User from department with unlimited quota (0 = unlimited) sends a message  
**Expected Behavior**: Request proceeds without quota checks

**Steps**:
1. Configure Department D with unlimited quota (monthly_limit_tokens = 0)
2. Send message as user from Department D
3. **Expected Response**:
   - Request succeeds normally
   - No quota warnings or errors
   - Usage tracking continues for analytics

**Validation**:
- [ ] Request succeeds regardless of current usage
- [ ] No quota status displayed (or shows "Unlimited")
- [ ] Usage still logged for analytics
- [ ] No quota enforcement applied

### Test Group 2: Token Estimation and Accuracy

#### Test 2.1: Token Estimation Accuracy
**Scenario**: Test the accuracy of token estimation vs actual usage  
**Expected Behavior**: Estimation should be reasonably accurate (within 20%)

**Steps**:
1. Send various length messages and compare estimated vs actual tokens:
   - Short message (10 words): "Hello, how are you today?"
   - Medium message (50 words): [Sample paragraph]
   - Long message (200 words): [Sample essay]
2. Compare `estimated_tokens` in request vs `actual_tokens` in response

**Validation**:
- [ ] Estimation within 20% of actual usage for most cases
- [ ] No requests blocked due to over-estimation
- [ ] Conservative estimation (slightly over-estimates rather than under)

#### Test 2.2: Edge Case Token Estimation
**Scenario**: Test token estimation for edge cases  
**Expected Behavior**: System handles edge cases gracefully

**Test Cases**:
- Empty message: ""
- Very long message (1000+ words)
- Message with special characters and emojis
- Message in non-English languages

**Validation**:
- [ ] Minimum token estimation applied (e.g., 100 tokens)
- [ ] Very long messages estimated appropriately
- [ ] Special characters handled correctly
- [ ] Non-English content estimated reasonably

### Test Group 3: Error Handling and Recovery

#### Test 3.1: Quota Service Unavailable
**Scenario**: Quota service fails or is unavailable  
**Expected Behavior**: Graceful fallback behavior

**Steps**:
1. Simulate quota service failure (mock error)
2. Attempt to send chat message
3. **Expected Response**:
   - Falls back to basic quota checking
   - Or allows request with logging (depending on configuration)
   - User receives appropriate error message

**Validation**:
- [ ] System doesn't crash or hang
- [ ] Appropriate fallback behavior
- [ ] User receives helpful error message
- [ ] System recovers when quota service is restored

#### Test 3.2: Database Connection Issues
**Scenario**: Database connection issues during quota check  
**Expected Behavior**: Appropriate error handling and user feedback

**Steps**:
1. Simulate database connection failure
2. Attempt quota operations
3. Monitor error handling and recovery

**Validation**:
- [ ] Graceful error handling
- [ ] No data corruption
- [ ] Appropriate user error messages
- [ ] System recovery after database restoration

---

## Phase 2: Frontend Error Handling Testing

### Test Group 4: Chat Interface Quota Integration

#### Test 4.1: QuotaStatusIndicator Display
**Scenario**: Test quota status indicator in various states  
**Expected Behavior**: Accurate real-time quota display

**Steps**:
1. Test indicator with different quota states:
   - Healthy (green): <80% usage
   - Warning (yellow): 80-100% usage
   - Exceeded (red): >100% usage
   - Unlimited (gray): No quota limits
2. Verify compact vs detailed view modes

**Validation**:
- [ ] Colors match quota status correctly
- [ ] Percentages calculated accurately
- [ ] Compact view shows essential info
- [ ] Detailed view shows comprehensive stats
- [ ] Refresh functionality works
- [ ] Tooltips and help text display correctly

#### Test 4.2: Message Input Quota Awareness
**Scenario**: Test message input behavior based on quota status  
**Expected Behavior**: Input adapts to quota constraints

**Steps**:
1. Test message input with different quota states
2. Verify placeholder text changes
3. Test send button state management
4. Test token estimation display

**Validation**:
- [ ] Placeholder text reflects quota status
- [ ] Send button disabled when quota exceeded
- [ ] Token estimation shown for large messages
- [ ] Warning messages appear for approaching limits

#### Test 4.3: Error Message Display and Actions
**Scenario**: Test error message presentation and user actions  
**Expected Behavior**: Clear error messages with actionable options

**Test Cases**:
- Quota exceeded error: Clear message + Contact Admin button
- Quota warning: Warning banner + Continue option
- Service unavailable: Retry option + Status message

**Validation**:
- [ ] Error messages are user-friendly
- [ ] Contact Admin functionality works
- [ ] Retry mechanisms function correctly
- [ ] Error states clear appropriately

### Test Group 5: Real-time Updates and Refresh

#### Test 5.1: Auto-refresh Quota Status
**Scenario**: Test automatic quota status updates  
**Expected Behavior**: Status updates without manual refresh

**Steps**:
1. Open chat interface
2. In separate tab/session, modify quota (admin)
3. Verify auto-refresh in original chat interface
4. Test various update intervals

**Validation**:
- [ ] Quota status updates automatically
- [ ] Updates don't interrupt user typing
- [ ] Network errors handled gracefully
- [ ] Update frequency is appropriate

#### Test 5.2: Multi-tab Consistency
**Scenario**: Test quota status consistency across multiple tabs  
**Expected Behavior**: Consistent quota display across sessions

**Steps**:
1. Open chat interface in multiple tabs
2. Send messages in one tab
3. Verify quota updates in other tabs
4. Test with different users/departments

**Validation**:
- [ ] Quota status syncs across tabs
- [ ] Usage updates reflected consistently
- [ ] No conflicting quota information

---

## Phase 3: Admin Monitoring Testing

### Test Group 6: Usage Monitoring Dashboard

#### Test 6.1: Real-time Metrics Display
**Scenario**: Test real-time usage metrics in admin dashboard  
**Expected Behavior**: Accurate, up-to-date metrics display

**Steps**:
1. Log in as admin user
2. Navigate to AdminSettings > Usage Monitor
3. Verify real-time metrics:
   - Active users count
   - Requests per minute
   - Tokens per minute
   - System health score

**Validation**:
- [ ] Metrics update in real-time (30-second intervals)
- [ ] Numbers match actual system activity
- [ ] Charts and graphs display correctly
- [ ] Health score calculation is accurate

#### Test 6.2: Department Usage Statistics
**Scenario**: Test department-level usage monitoring  
**Expected Behavior**: Comprehensive department analytics

**Steps**:
1. View department usage statistics
2. Verify data for each test department
3. Test quota status indicators
4. Check user activity within departments

**Validation**:
- [ ] All departments displayed correctly
- [ ] Usage percentages calculated accurately
- [ ] Quota status colors match actual state
- [ ] Department user counts are correct
- [ ] Last activity timestamps are accurate

#### Test 6.3: Usage Alerts System
**Scenario**: Test automated usage alerts and notifications  
**Expected Behavior**: Timely and accurate alert generation

**Steps**:
1. Monitor alert generation for quota events
2. Test alert severity levels
3. Verify alert details and metadata
4. Test "mark as read" functionality

**Validation**:
- [ ] Alerts generated for quota exceeded events
- [ ] Warning alerts for 80%+ usage
- [ ] Alert severity levels appropriate
- [ ] Alert timestamps accurate
- [ ] Mark as read functionality works

### Test Group 7: Admin Actions and Export

#### Test 7.1: Usage Data Export
**Scenario**: Test usage data export functionality  
**Expected Behavior**: Complete and accurate data export

**Steps**:
1. Click "Export" button in usage monitoring
2. Verify export process and file generation
3. Check exported data completeness
4. Test different time ranges and filters

**Validation**:
- [ ] Export process completes successfully
- [ ] Data accuracy in exported files
- [ ] Proper formatting (CSV, Excel, etc.)
- [ ] Email notification sent (if configured)
- [ ] File contains expected data fields

#### Test 7.2: Quota Management Integration
**Scenario**: Test integration between usage monitoring and quota management  
**Expected Behavior**: Seamless navigation and data consistency

**Steps**:
1. View usage monitoring dashboard
2. Navigate to quota management from usage alerts
3. Modify quotas and verify impact on usage display
4. Test bulk quota operations

**Validation**:
- [ ] Navigation between sections works smoothly
- [ ] Data consistency between monitoring and management
- [ ] Quota changes reflected in usage displays
- [ ] No data conflicts or inconsistencies

---

## Performance and Load Testing

### Test Group 8: Performance Under Load

#### Test 8.1: Concurrent User Quota Checks
**Scenario**: Test quota system performance with multiple concurrent users  
**Expected Behavior**: System handles concurrent requests efficiently

**Steps**:
1. Simulate 50+ concurrent chat requests
2. Monitor quota check response times
3. Verify quota accuracy under load
4. Check for race conditions

**Validation**:
- [ ] Quota checks complete within 500ms
- [ ] No quota miscalculations under load
- [ ] No race conditions in usage updates
- [ ] System remains responsive

#### Test 8.2: Database Performance
**Scenario**: Test database performance for quota operations  
**Expected Behavior**: Efficient database queries and updates

**Steps**:
1. Monitor database query performance
2. Test with large usage log datasets
3. Verify indexing efficiency
4. Check query optimization

**Validation**:
- [ ] Quota queries execute quickly (<100ms)
- [ ] Database indexes used effectively
- [ ] No database locks or deadlocks
- [ ] Memory usage remains stable

---

## Integration Testing Scenarios

### Test Group 9: End-to-End Workflows

#### Test 9.1: Complete User Journey - Normal Usage
**Scenario**: Test complete user experience from login to chat completion  
**Expected Behavior**: Smooth user experience with appropriate quota feedback

**Steps**:
1. User login → Dashboard → Chat Interface
2. Check quota status display
3. Send multiple messages
4. Monitor quota updates
5. Logout and re-login to verify persistence

**Validation**:
- [ ] Quota status displays correctly throughout journey
- [ ] Usage tracking works end-to-end
- [ ] Data persists across sessions
- [ ] No UI glitches or errors

#### Test 9.2: Complete Admin Journey - Quota Management
**Scenario**: Test complete admin workflow for quota management  
**Expected Behavior**: Comprehensive quota management capabilities

**Steps**:
1. Admin login → AdminSettings → Usage Monitor
2. Identify departments approaching limits
3. Navigate to quota management
4. Adjust quotas for departments
5. Verify changes in monitoring dashboard

**Validation**:
- [ ] Admin workflow is intuitive and efficient
- [ ] Data updates propagate correctly
- [ ] All admin features function properly
- [ ] Changes reflected in user experience

#### Test 9.3: Quota Exceeded Recovery Scenario
**Scenario**: Test system behavior during quota exceeded and recovery  
**Expected Behavior**: Graceful handling of quota exceeded state and recovery

**Steps**:
1. User hits quota limit
2. Admin increases quota
3. User can resume normal usage
4. System tracking continues correctly

**Validation**:
- [ ] Quota exceeded state handled gracefully
- [ ] Quota increase takes effect immediately
- [ ] User can resume usage without restart
- [ ] No data loss or corruption

---

## Browser and Device Testing

### Test Group 10: Cross-platform Compatibility

#### Test 10.1: Browser Compatibility
**Scenario**: Test quota features across different browsers  
**Expected Behavior**: Consistent behavior across all major browsers

**Browsers to Test**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Validation**:
- [ ] Quota indicators display correctly in all browsers
- [ ] Real-time updates work across browsers
- [ ] Error handling consistent across browsers
- [ ] No browser-specific issues

#### Test 10.2: Mobile Responsiveness
**Scenario**: Test quota interface on mobile devices  
**Expected Behavior**: Mobile-friendly quota displays and interactions

**Steps**:
1. Test chat interface on mobile browsers
2. Verify quota status indicator responsiveness
3. Test admin monitoring dashboard on mobile
4. Check touch interactions and gestures

**Validation**:
- [ ] Quota indicators scale appropriately for mobile
- [ ] Touch interactions work smoothly
- [ ] Text remains readable on small screens
- [ ] No horizontal scrolling issues

---

## Security Testing

### Test Group 11: Security and Authorization

#### Test 11.1: Quota Access Control
**Scenario**: Test quota information access controls  
**Expected Behavior**: Users can only access their department's quota information

**Steps**:
1. Test cross-department quota access attempts
2. Verify admin-only quota management access
3. Test API endpoint authorization
4. Check for information leakage

**Validation**:
- [ ] Users cannot access other departments' quota info
- [ ] Non-admin users cannot modify quotas
- [ ] API endpoints properly authorized
- [ ] No sensitive information leaked in errors

#### Test 11.2: Quota Manipulation Prevention
**Scenario**: Test prevention of quota manipulation  
**Expected Behavior**: Quota values cannot be manipulated by unauthorized users

**Steps**:
1. Attempt direct API calls to modify quotas
2. Test client-side manipulation attempts
3. Verify server-side validation
4. Check audit trail for quota changes

**Validation**:
- [ ] Quota modifications require proper authorization
- [ ] Client-side manipulation prevented
- [ ] Server-side validation enforced
- [ ] All quota changes logged appropriately

---

## Test Execution Checklist

### Pre-Testing Setup
- [ ] Backend server running and accessible
- [ ] Frontend application deployed and accessible
- [ ] Database populated with test data
- [ ] Test user accounts created and configured
- [ ] LLM configurations enabled and functional
- [ ] Quota configurations set up for test scenarios

### Test Execution
- [ ] Backend quota enforcement tests (Tests 1.1-3.2)
- [ ] Frontend error handling tests (Tests 4.1-5.2)
- [ ] Admin monitoring tests (Tests 6.1-7.2)
- [ ] Performance and load tests (Tests 8.1-8.2)
- [ ] Integration tests (Tests 9.1-9.3)
- [ ] Browser compatibility tests (Tests 10.1-10.2)
- [ ] Security tests (Tests 11.1-11.2)

### Post-Testing Validation
- [ ] All test cases executed successfully
- [ ] Critical bugs identified and documented
- [ ] Performance benchmarks met
- [ ] Security requirements validated
- [ ] User experience requirements satisfied

---

## Success Criteria

The AID-US-007 quota enforcement system is considered fully tested and ready for production when:

### Functional Requirements ✅
- [ ] Pre-request quota validation prevents overruns
- [ ] Users receive clear quota status feedback
- [ ] Admins can monitor usage in real-time
- [ ] Error handling is user-friendly and informative
- [ ] Token estimation is reasonably accurate

### Performance Requirements ✅
- [ ] Quota checks complete within 500ms
- [ ] System handles 50+ concurrent users
- [ ] Real-time updates work without noticeable lag
- [ ] Database queries are optimized and efficient

### Security Requirements ✅
- [ ] Quota information is properly secured
- [ ] Authorization controls prevent unauthorized access
- [ ] No quota manipulation vulnerabilities
- [ ] Audit trail for all quota-related actions

### User Experience Requirements ✅
- [ ] Interface is intuitive and responsive
- [ ] Error messages are clear and actionable
- [ ] Quota status is visible and understandable
- [ ] Admin tools are comprehensive and easy to use

---

## Bug Reporting Template

When issues are found during testing, use this template:

```markdown
## Bug Report

**Test Case**: [Test ID and description]
**Priority**: Critical/High/Medium/Low
**Browser/Device**: [Browser version and device info]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result**: [What should happen]
**Actual Result**: [What actually happened]
**Screenshots**: [If applicable]

**Additional Notes**: [Any other relevant information]
```

---

## Testing Completion

**Testing Started**: [Date]  
**Testing Completed**: [Date]  
**Total Test Cases**: 40+  
**Test Cases Passed**: [Number]  
**Critical Issues Found**: [Number]  
**Ready for Production**: [Yes/No]

**Sign-off**:
- QA Lead: [Name and Date]
- Development Lead: [Name and Date]  
- Product Owner: [Name and Date]

---

*This comprehensive testing guide ensures that the AID-US-007 quota enforcement system is thoroughly validated before production deployment. All test scenarios should be executed and documented for a complete quality assurance process.*
