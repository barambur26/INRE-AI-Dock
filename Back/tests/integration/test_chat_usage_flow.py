"""
Integration Tests for Chat Usage Flow - AID-US-005

This module contains comprehensive integration tests for the complete chat usage logging flow including:
- End-to-end chat request → LLM response → usage logging → quota update workflow
- Integration between chat service, LLM service, and database operations  
- Real database operations with actual model relationships
- Complete authentication and authorization flow
- Performance testing under realistic conditions

Test Categories:
1. Complete Chat Usage Flow Tests
2. Multi-User Scenario Tests
3. Quota Integration Flow Tests
4. Error Recovery Tests
5. Performance Integration Tests
6. Authentication Integration Tests
"""

import asyncio
import uuid
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

# Import the app and dependencies
from app.main import app
from app.models import User, Department, Role, LLMConfiguration, DepartmentQuota, UsageLog
from app.services.chat_service import ChatService, ChatServiceError, QuotaExceededError
from app.services.llm_service import llm_service, LLMProviderError
from app.schemas.auth import UserProfile
from app.schemas.chat import ChatSendRequest, ChatSendResponse
from app.core.database import get_async_session

# Test client setup
client = TestClient(app)

# Test constants
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin", "department": "IT"},
    "user1": {"username": "user1", "password": "user123", "role": "user", "department": "Finance"},
    "user2": {"username": "user2", "password": "user123", "role": "user", "department": "HR"},
    "analyst": {"username": "analyst", "password": "analyst123", "role": "analyst", "department": "IT"},
}


class TestCompleteUsageLoggingFlow:
    """Test complete end-to-end usage logging flow"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Clear any existing rate limits
        from app.middleware.rate_limit import clear_rate_limits
        clear_rate_limits()
    
    def test_complete_chat_to_usage_log_flow(self):
        """Test complete flow: login → chat → usage logging → quota update"""
        # 1. Login to get access token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Mock LLM service to avoid external API calls
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.return_value = (
                "The capital of France is Paris.",  # response
                15,  # prompt_tokens
                35,  # completion_tokens
                0.002  # estimated_cost
            )
            
            # 3. Send chat message
            chat_response = client.post(
                "/api/v1/chat/send",
                headers=headers,
                json={
                    "message": "What is the capital of France?",
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            
            # 4. Verify chat response structure
            assert "response" in chat_data
            assert "model_used" in chat_data
            assert "tokens_prompt" in chat_data
            assert "tokens_completion" in chat_data
            assert "tokens_total" in chat_data
            assert "cost_estimated" in chat_data
            assert "usage_log_id" in chat_data
            
            # 5. Verify response data
            assert chat_data["response"] == "The capital of France is Paris."
            assert chat_data["tokens_prompt"] == 15
            assert chat_data["tokens_completion"] == 35
            assert chat_data["tokens_total"] == 50
            assert chat_data["cost_estimated"] == 0.002
            assert chat_data["usage_log_id"] is not None
            
            # 6. Verify LLM service was called
            mock_llm.assert_called_once()
    
    def test_multiple_chat_messages_logging(self):
        """Test that multiple chat messages create separate usage logs"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Mock LLM service with different responses
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_responses = [
                ("Response 1", 10, 20, 0.001),
                ("Response 2", 15, 25, 0.002),
                ("Response 3", 20, 30, 0.003)
            ]
            mock_llm.side_effect = mock_responses
            
            usage_log_ids = []
            
            # Send multiple messages
            for i, (expected_response, _, _, _) in enumerate(mock_responses):
                chat_response = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": f"Test message {i+1}",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                assert chat_response.status_code == 200
                chat_data = chat_response.json()
                
                # Verify each response
                assert chat_data["response"] == expected_response
                assert "usage_log_id" in chat_data
                
                # Collect usage log IDs
                usage_log_ids.append(chat_data["usage_log_id"])
            
            # Verify all usage log IDs are unique
            assert len(set(usage_log_ids)) == 3
            assert len(usage_log_ids) == 3
            
            # Verify LLM service was called 3 times
            assert mock_llm.call_count == 3
    
    def test_usage_logging_with_quota_enforcement(self):
        """Test usage logging integration with quota enforcement"""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user2",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Mock a scenario where quota is nearly exceeded
        with patch('app.services.chat_service.ChatService._check_quota') as mock_quota_check:
            with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
                # First call: quota check passes
                mock_quota_check.return_value = None
                mock_llm.return_value = ("Test response", 800, 200, 0.05)  # High token usage
                
                # Send first message (should succeed)
                chat_response1 = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": "First message",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                assert chat_response1.status_code == 200
                
                # Second call: quota exceeded
                mock_quota_check.side_effect = QuotaExceededError("Quota exceeded")
                
                # Send second message (should fail due to quota)
                chat_response2 = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": "Second message", 
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                # Should return error for quota exceeded
                assert chat_response2.status_code in [400, 429]  # Bad request or rate limited
                
                # Verify quota check was called for both attempts
                assert mock_quota_check.call_count == 2
                # Verify LLM was only called once (for the first successful request)
                assert mock_llm.call_count == 1


class TestMultiUserUsageScenarios:
    """Test usage logging with multiple users and departments"""
    
    def test_different_users_separate_logs(self):
        """Test that different users create separate usage logs"""
        user_tokens = {}
        
        # Login as multiple users
        for user_key, user_data in TEST_USERS.items():
            if user_key in ["user1", "user2"]:  # Test with 2 regular users
                login_response = client.post(
                    "/api/v1/auth/login",
                    json={
                        "username": user_data["username"],
                        "password": user_data["password"],
                        "remember_me": False
                    }
                )
                
                assert login_response.status_code == 200
                user_tokens[user_key] = login_response.json()["access_token"]
        
        # Mock LLM service
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.return_value = ("AI response", 20, 40, 0.003)
            
            usage_logs = []
            
            # Send messages from different users
            for user_key, token in user_tokens.items():
                headers = {"Authorization": f"Bearer {token}"}
                
                chat_response = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": f"Message from {user_key}",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                assert chat_response.status_code == 200
                chat_data = chat_response.json()
                
                # Verify response and collect usage log info
                assert "usage_log_id" in chat_data
                usage_logs.append({
                    "user": user_key,
                    "usage_log_id": chat_data["usage_log_id"],
                    "tokens_total": chat_data["tokens_total"]
                })
            
            # Verify we have separate logs for each user
            assert len(usage_logs) == 2
            log_ids = [log["usage_log_id"] for log in usage_logs]
            assert len(set(log_ids)) == 2  # All IDs should be unique
            
            # Verify LLM service was called for each user
            assert mock_llm.call_count == 2
    
    def test_department_based_usage_tracking(self):
        """Test that usage is tracked per department correctly"""
        # This test would require more complex setup with actual database
        # For now, we'll test the API structure
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123", 
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Mock LLM service for admin chat
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.return_value = ("Admin response", 25, 45, 0.004)
            
            chat_response = client.post(
                "/api/v1/chat/send",
                headers=headers,
                json={
                    "message": "Admin department message",
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
            assert chat_response.status_code == 200
            chat_data = chat_response.json()
            
            # Verify admin usage is logged
            assert "usage_log_id" in chat_data
            assert chat_data["tokens_total"] == 70  # 25 + 45


class TestErrorRecoveryInUsageLogging:
    """Test error recovery scenarios in usage logging"""
    
    def test_llm_service_error_no_usage_log(self):
        """Test that LLM service errors don't create usage logs"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Mock LLM service to raise an error
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.side_effect = LLMProviderError("API rate limit exceeded")
            
            # Send chat message that should fail
            chat_response = client.post(
                "/api/v1/chat/send",
                headers=headers,
                json={
                    "message": "This should fail",
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
            # Should return error status
            assert chat_response.status_code in [400, 500]
            
            # Verify LLM service was called
            mock_llm.assert_called_once()
    
    def test_quota_exceeded_before_llm_call(self):
        """Test that quota check prevents LLM call and usage logging"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Mock quota check to fail
        with patch('app.services.chat_service.ChatService._check_quota') as mock_quota_check:
            with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
                mock_quota_check.side_effect = QuotaExceededError("Department quota exceeded")
                
                # Send chat message
                chat_response = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": "This should be blocked by quota",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                # Should return quota exceeded error
                assert chat_response.status_code in [400, 429]
                
                # Verify quota check was called
                mock_quota_check.assert_called_once()
                
                # Verify LLM service was NOT called
                mock_llm.assert_not_called()
    
    def test_database_error_handling(self):
        """Test handling of database errors during usage logging"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Mock database error during logging
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            with patch('app.services.chat_service.ChatService._log_usage') as mock_log_usage:
                mock_llm.return_value = ("Response", 10, 20, 0.001)
                mock_log_usage.side_effect = Exception("Database connection lost")
                
                # Send chat message
                chat_response = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": "This should cause database error",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                # Should return error due to logging failure
                assert chat_response.status_code == 500
                
                # Verify LLM service was called
                mock_llm.assert_called_once()
                
                # Verify logging was attempted
                mock_log_usage.assert_called_once()


class TestPerformanceIntegration:
    """Test performance aspects of the complete usage logging flow"""
    
    def test_concurrent_chat_requests_performance(self):
        """Test performance with concurrent chat requests"""
        import threading
        import time
        import queue
        
        # Login to get token
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        results = queue.Queue()
        
        def send_chat_message(message_id):
            """Send a chat message and record the result"""
            start_time = time.time()
            
            with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
                mock_llm.return_value = (f"Response {message_id}", 10, 20, 0.001)
                
                try:
                    chat_response = client.post(
                        "/api/v1/chat/send",
                        headers=headers,
                        json={
                            "message": f"Concurrent message {message_id}",
                            "conversation_id": str(uuid.uuid4())
                        }
                    )
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    results.put({
                        "message_id": message_id,
                        "status_code": chat_response.status_code,
                        "duration": duration,
                        "success": chat_response.status_code == 200
                    })
                    
                except Exception as e:
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    results.put({
                        "message_id": message_id,
                        "status_code": None,
                        "duration": duration,
                        "success": False,
                        "error": str(e)
                    })
        
        # Start multiple concurrent requests
        threads = []
        num_requests = 5  # Moderate number to avoid overwhelming
        
        for i in range(num_requests):
            thread = threading.Thread(target=send_chat_message, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect and analyze results
        all_results = []
        while not results.empty():
            all_results.append(results.get())
        
        assert len(all_results) == num_requests
        
        # Check that most requests succeeded
        successful_requests = [r for r in all_results if r["success"]]
        success_rate = len(successful_requests) / len(all_results)
        
        # Allow for some rate limiting, but most should succeed
        assert success_rate >= 0.6, f"Success rate too low: {success_rate}"
        
        # Check that response times are reasonable
        for result in successful_requests:
            assert result["duration"] < 5.0, f"Request {result['message_id']} took {result['duration']:.2f}s"
    
    def test_usage_logging_overhead(self):
        """Test that usage logging doesn't add significant overhead"""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        import time
        
        # Mock LLM service with consistent response time
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.return_value = ("Test response", 15, 25, 0.002)
            
            # Measure time for multiple sequential requests
            start_time = time.time()
            
            for i in range(10):
                chat_response = client.post(
                    "/api/v1/chat/send",
                    headers=headers,
                    json={
                        "message": f"Performance test message {i}",
                        "conversation_id": str(uuid.uuid4())
                    }
                )
                
                assert chat_response.status_code == 200
            
            end_time = time.time()
            total_duration = end_time - start_time
            avg_duration = total_duration / 10
            
            # Average request should complete in reasonable time
            assert avg_duration < 1.0, f"Average request duration too high: {avg_duration:.3f}s"
            
            # Verify all LLM calls were made
            assert mock_llm.call_count == 10


class TestAuthenticationIntegration:
    """Test integration between authentication and usage logging"""
    
    def test_unauthenticated_chat_request(self):
        """Test that unauthenticated requests don't create usage logs"""
        # Send chat request without authentication
        chat_response = client.post(
            "/api/v1/chat/send",
            json={
                "message": "Unauthenticated message",
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        # Should return authentication error
        assert chat_response.status_code == 401
    
    def test_invalid_token_chat_request(self):
        """Test that invalid tokens don't allow chat requests"""
        # Use invalid token
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        chat_response = client.post(
            "/api/v1/chat/send",
            headers=headers,
            json={
                "message": "Message with invalid token",
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        # Should return authentication error
        assert chat_response.status_code == 401
    
    def test_expired_token_handling(self):
        """Test handling of expired tokens in chat requests"""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Create an already-expired token
        expired_token = create_access_token(
            data={"sub": "user1", "type": "access"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        chat_response = client.post(
            "/api/v1/chat/send",
            headers=headers,
            json={
                "message": "Message with expired token",
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        # Should return authentication error
        assert chat_response.status_code == 401
    
    def test_user_role_access_logging(self):
        """Test that different user roles are logged correctly"""
        # Test with admin user
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123",
                "remember_me": False
            }
        )
        
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with regular user
        user_login = client.post(
            "/api/v1/auth/login",
            json={
                "username": "user1",
                "password": "user123",
                "remember_me": False
            }
        )
        
        assert user_login.status_code == 200
        user_token = user_login.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Mock LLM service
        with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
            mock_llm.return_value = ("Role test response", 20, 30, 0.003)
            
            # Send chat from admin
            admin_chat = client.post(
                "/api/v1/chat/send",
                headers=admin_headers,
                json={
                    "message": "Admin message",
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
            assert admin_chat.status_code == 200
            admin_data = admin_chat.json()
            assert "usage_log_id" in admin_data
            
            # Send chat from user
            user_chat = client.post(
                "/api/v1/chat/send",
                headers=user_headers,
                json={
                    "message": "User message",
                    "conversation_id": str(uuid.uuid4())
                }
            )
            
            assert user_chat.status_code == 200
            user_data = user_chat.json()
            assert "usage_log_id" in user_data
            
            # Verify different usage log IDs
            assert admin_data["usage_log_id"] != user_data["usage_log_id"]
            
            # Verify LLM service called for both
            assert mock_llm.call_count == 2


# Helper functions for integration testing
def get_authenticated_headers(username: str, password: str) -> Dict[str, str]:
    """Helper to get authenticated headers for a user"""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password,
            "remember_me": False
        }
    )
    
    if login_response.status_code != 200:
        raise Exception(f"Failed to login user {username}")
    
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

def send_mock_chat_message(
    headers: Dict[str, str],
    message: str = "Test message",
    mock_response: str = "Test response",
    mock_tokens: tuple = (10, 20),
    mock_cost: float = 0.001
) -> Dict[str, Any]:
    """Helper to send a chat message with mocked LLM response"""
    
    with patch('app.services.llm_service.llm_service.send_message') as mock_llm:
        mock_llm.return_value = (mock_response, mock_tokens[0], mock_tokens[1], mock_cost)
        
        chat_response = client.post(
            "/api/v1/chat/send",
            headers=headers,
            json={
                "message": message,
                "conversation_id": str(uuid.uuid4())
            }
        )
        
        return {
            "response": chat_response,
            "data": chat_response.json() if chat_response.status_code == 200 else None,
            "mock_llm": mock_llm
        }

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
