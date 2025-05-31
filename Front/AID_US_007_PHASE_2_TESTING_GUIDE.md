# AID-US-007 Phase 2 Testing Guide
## Frontend Error Handling & Enhanced Quota Enforcement

### Overview
This guide provides comprehensive testing scenarios for Phase 2 of AID-US-007, which implements enhanced frontend error handling, real-time quota monitoring, and improved user experience for quota enforcement.

### Prerequisites
- Backend Phase 1 (quota enforcement logic) must be completed and running
- Frontend application running on http://localhost:8080
- Backend API running on http://localhost:8000
- At least one admin user and one regular user configured
- At least one LLM model configured and enabled
- Department quotas configured for testing

---

## Testing Scenarios

### 1. Enhanced Chat Error Handling

#### 1.1 Quota Exceeded Error Display
**Test Steps:**
1. Set a very low quota limit (e.g., 100 tokens) for a test department
2. Login as a user in that department
3. Navigate to Chat Interface
4. Send messages until quota is exceeded
5. Attempt to send another message

**Expected Results:**
- ✅ Red error banner appears with "Quota Issue" header
- ✅ Clear error message explaining quota exceeded
- ✅ Suggested actions list appears (contact admin, wait for reset)
- ✅ "Contact Admin" button opens email composition
- ✅ Message input field is disabled with "Quota exceeded" placeholder
- ✅ User message is removed from conversation if send fails

#### 1.2 Quota Warning Display
**Test Steps:**
1. Set a quota where current usage is 80-95% of limit
2. Login as user in that department
3. Navigate to Chat Interface
4. Type a message that would approach the quota limit

**Expected Results:**
- ✅ Yellow warning banner appears before sending
- ✅ Token estimation shows for message
- ✅ Warning explains percentage of remaining quota the message will use
- ✅ Message can still be sent
- ✅ Quota status updates after successful send

#### 1.3 Network Error Handling
**Test Steps:**
1. Login to chat interface
2. Stop the backend server
3. Try to send a message
4. Restart backend server
5. Click "Retry" button

**Expected Results:**
- ✅ Yellow error banner appears with "Connection Issue"
- ✅ Network-specific error message displayed
- ✅ "Retry" button appears and works when server is back online
- ✅ Interface recovers gracefully when connection restored

### 2. Real-Time Quota Status Components

#### 2.1 QuotaStatusIndicator - Compact View
**Test Steps:**
1. Login and navigate to Chat Interface
2. Observe the compact quota indicator in ModelIndicator
3. Hover over the compact indicator
4. Test with different quota usage levels (0-50%, 50-80%, 80-95%, 95-100%, exceeded)

**Expected Results:**
- ✅ Color-coded indicator (green/yellow/red) based on usage
- ✅ Shows usage percentage and remaining tokens
- ✅ Tooltip appears on hover with detailed information
- ✅ Updates automatically when quota usage changes

#### 2.2 QuotaStatusIndicator - Detailed View
**Test Steps:**
1. In Chat Interface, click the expand button in ModelIndicator
2. Review the detailed quota status panel
3. Test "Refresh" button functionality
4. Test different quota states

**Expected Results:**
- ✅ Detailed quota information panel expands/collapses
- ✅ Progress bar shows visual quota usage
- ✅ Statistics grid shows remaining tokens and estimated time
- ✅ Department information displayed
- ✅ Appropriate warning/error messages for quota status
- ✅ "Contact Admin" button appears when quota exceeded
- ✅ "Refresh" button updates quota information

#### 2.3 Enhanced ModelIndicator Integration
**Test Steps:**
1. Navigate to Chat Interface
2. Expand/collapse quota details using chevron button
3. Test with different model states (enabled/disabled)
4. Test with different quota states

**Expected Results:**
- ✅ Model information clearly displayed with provider badge
- ✅ Compact quota status integrated seamlessly
- ✅ Expandable quota details work smoothly
- ✅ Warning messages appear for disabled models
- ✅ Proper spacing and layout maintained

### 3. Chat Service Integration

#### 3.1 Enhanced Error Methods Integration
**Test Steps:**
1. Login and navigate to Chat Interface
2. Trigger different error types (quota, network, LLM)
3. Verify error formatting and suggestions

**Expected Results:**
- ✅ ChatService.formatErrorMessage() provides user-friendly messages
- ✅ ChatService.getErrorSuggestions() returns relevant action items
- ✅ ChatService.isQuotaError() correctly identifies quota errors
- ✅ Quota information extracted from errors when available

#### 3.2 Real-Time Quota Monitoring
**Test Steps:**
1. Login to Chat Interface
2. Send several messages and observe quota updates
3. Verify automatic quota refresh (every 30 seconds)
4. Test manual quota refresh functionality

**Expected Results:**
- ✅ Quota information updates after each message
- ✅ Automatic refresh occurs every 30 seconds when active
- ✅ Manual refresh button updates quota immediately
- ✅ Last updated timestamp shows in footer
- ✅ Quota warnings appear when approaching limits

### 4. Enhanced User Experience

#### 4.1 Quota-Aware MessageInput
**Test Steps:**
1. Navigate to Chat Interface with different quota levels
2. Type messages of varying lengths
3. Observe token estimation and warnings
4. Test with quota exceeded state

**Expected Results:**
- ✅ Token estimation appears for longer messages (>50 characters)
- ✅ Warning banner shows when message would use significant quota
- ✅ Character counter and quota remaining displayed
- ✅ Input styling changes based on quota status (red/yellow borders)
- ✅ Helpful tips and guidance appear based on state
- ✅ Input disabled appropriately when quota exceeded

#### 4.2 Contact Admin Functionality
**Test Steps:**
1. Trigger quota exceeded state
2. Click "Contact Admin" buttons in various locations
3. Verify email composition

**Expected Results:**
- ✅ Email composition opens with pre-filled subject
- ✅ Email body includes relevant quota information
- ✅ Department details included in email template
- ✅ Professional, helpful tone in email template

#### 4.3 Graceful Degradation
**Test Steps:**
1. Test chat interface with no quota information available
2. Test with network connectivity issues
3. Test with disabled models
4. Test loading states

**Expected Results:**
- ✅ Interface remains functional when quota info unavailable
- ✅ Appropriate loading states shown during data fetching
- ✅ Clear messaging when services are unavailable
- ✅ Fallback states don't break interface functionality

### 5. Integration Testing

#### 5.1 Complete Chat Flow with Quota Enforcement
**Test Steps:**
1. Login as regular user
2. Navigate to Chat Interface
3. Send messages progressively approaching quota limit
4. Observe warnings and status changes
5. Exceed quota and verify blocking
6. Test as admin user (should have different experience)

**Expected Results:**
- ✅ Smooth transition through quota warning levels
- ✅ Real-time status updates throughout conversation
- ✅ Proper message blocking when quota exceeded
- ✅ Admin users may have different quota rules
- ✅ All error states handle gracefully

#### 5.2 Cross-Component Communication
**Test Steps:**
1. Test quota status updates across all components
2. Verify error state synchronization
3. Test component interaction with refresh actions

**Expected Results:**
- ✅ Quota updates propagate to all displayed components
- ✅ Error states consistent across interface
- ✅ Refresh actions update all relevant displays
- ✅ Component state management works correctly

---

## Performance Testing

### 1. Real-Time Updates
**Test Steps:**
1. Open multiple chat interfaces in different tabs
2. Monitor automatic quota refresh performance
3. Test with high-frequency usage

**Expected Results:**
- ✅ Quota checks don't impact chat response times significantly
- ✅ Multiple tabs don't create excessive API calls
- ✅ Real-time updates work smoothly without UI lag

### 2. Error Handling Performance
**Test Steps:**
1. Trigger rapid error scenarios
2. Test error state transitions
3. Monitor memory usage during error conditions

**Expected Results:**
- ✅ Error handling doesn't cause memory leaks
- ✅ Error state transitions are smooth
- ✅ Interface remains responsive during error states

---

## Browser Compatibility Testing

### Test Matrix
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

### Mobile Responsiveness
- ✅ iPhone Safari
- ✅ Android Chrome
- ✅ Tablet displays

---

## Accessibility Testing

### 1. Screen Reader Compatibility
**Test Steps:**
1. Test with screen reader (NVDA/JAWS/VoiceOver)
2. Verify error announcements
3. Check quota status accessibility

**Expected Results:**
- ✅ Error messages are announced properly
- ✅ Quota status changes are communicated
- ✅ Button purposes are clear
- ✅ Form inputs have proper labels

### 2. Keyboard Navigation
**Test Steps:**
1. Navigate interface using only keyboard
2. Test all interactive elements
3. Verify focus management

**Expected Results:**
- ✅ All interactive elements reachable via keyboard
- ✅ Focus order is logical
- ✅ Error states don't trap focus
- ✅ Modal dialogs handle focus correctly

---

## Security Testing

### 1. Error Information Disclosure
**Test Steps:**
1. Trigger various error conditions
2. Verify no sensitive information leaked
3. Check network requests for data exposure

**Expected Results:**
- ✅ Error messages don't expose sensitive backend details
- ✅ Quota information doesn't reveal other users' data
- ✅ Network requests don't include unnecessary information

---

## Test Commands

### Frontend Testing
```bash
# Start frontend development server
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Front
npm run dev

# Run frontend tests (if available)
npm test

# Build for production testing
npm run build
```

### Backend Testing
```bash
# Start backend server
cd /Users/blas/Desktop/INRE/INRE-AI-Dock/Back
python -m uvicorn app.main:app --reload

# Test quota enforcement endpoints
curl -X GET "http://localhost:8000/api/v1/chat/quota" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Known Issues & Limitations

### Current Limitations
1. **Token Estimation**: Currently uses simple character-based estimation (4 chars/token)
2. **Real-time Updates**: 30-second interval may be too frequent for production
3. **Email Integration**: Uses mailto: links instead of integrated email service
4. **Offline Support**: Limited functionality when offline

### Future Enhancements
1. More accurate token estimation using tiktoken-style algorithms
2. WebSocket integration for real-time quota updates
3. Integrated email/notification service
4. Offline message queuing
5. Advanced quota analytics and predictions

---

## Completion Criteria

### Phase 2 is considered complete when:
- ✅ All 20+ test scenarios pass successfully
- ✅ Enhanced error handling works across all error types
- ✅ Real-time quota monitoring functions correctly
- ✅ User experience improvements are functional
- ✅ Cross-browser compatibility verified
- ✅ Accessibility requirements met
- ✅ Performance benchmarks achieved
- ✅ Security validation passed

### Ready for Phase 3 when:
- ✅ User acceptance testing completed
- ✅ No critical bugs identified
- ✅ Documentation updated
- ✅ Stakeholder approval received

---

**Last Updated:** May 30, 2025  
**Version:** 1.0  
**Author:** AI Development Assistant  
**Status:** Phase 2 Implementation Complete
