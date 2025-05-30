"""
Comprehensive Unit Tests for Usage Logging - AID-US-005

This module contains comprehensive unit tests for the usage logging system including:
- UsageLog model validation and relationships
- Chat service usage logging functionality
- Quota tracking integration
- Data integrity and validation
- Error handling scenarios

Test Categories:
1. UsageLog Model Tests
2. Chat Service Logging Tests  
3. Quota Integration Tests
4. Data Validation Tests
5. Error Handling Tests
6. Performance Tests
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

# Import models and services
from app.models import User, Department, Role, LLMConfiguration, DepartmentQuota, UsageLog
from app.services.chat_service import ChatService, ChatServiceError, QuotaExceededError
from app.schemas.auth import UserProfile
from app.schemas.chat import ChatSendRequest, ChatSendResponse


class TestUsageLogModel:
    """Test UsageLog model functionality and validation"""
    
    def test_usage_log_creation(self):
        """Test basic UsageLog model creation"""
        usage_log = UsageLog(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            tokens_prompt=150,
            tokens_completion=300,
            cost_estimated=Decimal('0.0075'),
            request_details={"message": "Test message", "conversation_id": "test-conv-1"},
            response_details={"response": "Test response", "model_used": "gpt-3.5-turbo"}
        )
        
        # Test basic properties
        assert usage_log.tokens_prompt == 150
        assert usage_log.tokens_completion == 300
        assert usage_log.cost_estimated == Decimal('0.0075')
        assert usage_log.request_details["message"] == "Test message"
        assert usage_log.response_details["response"] == "Test response"
        
        # Test computed property
        assert usage_log.tokens_total == 450  # 150 + 300
    
    def test_usage_log_required_fields(self):
        """Test that required fields are validated"""
        # Test missing user_id
        with pytest.raises(Exception):
            usage_log = UsageLog(
                department_id=uuid.uuid4(),
                llm_config_id=uuid.uuid4(),
                tokens_prompt=100,
                tokens_completion=200
            )
    
    def test_usage_log_defaults(self):
        """Test default values for optional fields"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test defaults
        assert usage_log.tokens_prompt == 0
        assert usage_log.tokens_completion == 0
        assert usage_log.cost_estimated == Decimal('0.0000')
        assert usage_log.request_details == {}
        assert usage_log.response_details == {}
        assert usage_log.timestamp is not None  # Should have a default timestamp
    
    def test_usage_log_relationships(self):
        """Test that relationships are properly defined"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test relationship attributes exist
        assert hasattr(usage_log, 'user')
        assert hasattr(usage_log, 'department')
        assert hasattr(usage_log, 'llm_config')
    
    def test_usage_log_repr(self):
        """Test string representation"""
        log_id = uuid.uuid4()
        user_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)
        
        usage_log = UsageLog(
            id=log_id,
            user_id=user_id,
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4(),
            timestamp=timestamp
        )
        
        repr_str = repr(usage_log)
        assert str(log_id) in repr_str
        assert str(user_id) in repr_str
        assert "UsageLog" in repr_str
    
    def test_tokens_total_calculation(self):
        """Test tokens_total hybrid property calculation"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4(),
            tokens_prompt=250,
            tokens_completion=750
        )
        
        assert usage_log.tokens_total == 1000
        
        # Test with zero values
        usage_log.tokens_prompt = 0
        usage_log.tokens_completion = 0
        assert usage_log.tokens_total == 0
        
        # Test with None values (should handle gracefully)
        usage_log.tokens_prompt = None
        usage_log.tokens_completion = 100
        # This should either work or raise a predictable error
        try:
            total = usage_log.tokens_total
            assert total == 100  # If None is treated as 0
        except TypeError:
            # If None causes TypeError, that's also acceptable
            pass


class TestChatServiceUsageLogging:
    """Test chat service usage logging functionality"""
    
    @pytest.fixture
    def mock_user_profile(self):
        """Create a mock user profile for testing"""
        return UserProfile(
            id=uuid.uuid4(),
            username="testuser",
            email="testuser@example.com",
            role="user",
            role_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            department_name="IT",
            is_active=True
        )
    
    @pytest.fixture
    def mock_chat_request(self):
        """Create a mock chat request for testing"""
        return ChatSendRequest(
            message="What is the capital of France?",
            conversation_id=uuid.uuid4(),
            model_id=None
        )
    
    @pytest.fixture
    def mock_llm_config(self):
        """Create a mock LLM configuration for testing"""
        return LLMConfiguration(
            id=uuid.uuid4(),
            model_name="gpt-3.5-turbo",
            provider="openai",
            enabled=True,
            config_json={"max_tokens": 2000, "temperature": 0.7}
        )
    
    @pytest.mark.asyncio
    async def test_log_usage_method(self, mock_user_profile, mock_llm_config):
        """Test the _log_usage method directly"""
        chat_service = ChatService()
        
        # Mock database session
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Test data
        prompt_tokens = 50
        completion_tokens = 150
        estimated_cost = 0.005
        request_details = {"message": "Test message", "user_message_length": 12}
        response_details = {"response": "Test response", "response_length": 13}
        
        # Call the method
        usage_log = await chat_service._log_usage(
            db=mock_db,
            user_id=mock_user_profile.id,
            department_id=mock_user_profile.department_id,
            llm_config_id=mock_llm_config.id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=estimated_cost,
            request_details=request_details,
            response_details=response_details
        )
        
        # Verify the usage log was created correctly
        assert usage_log.user_id == mock_user_profile.id
        assert usage_log.department_id == mock_user_profile.department_id
        assert usage_log.llm_config_id == mock_llm_config.id
        assert usage_log.tokens_prompt == prompt_tokens
        assert usage_log.tokens_completion == completion_tokens
        assert usage_log.cost_estimated == estimated_cost
        assert usage_log.request_details == request_details
        assert usage_log.response_details == response_details
        assert usage_log.timestamp is not None
        
        # Verify database operations were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_creates_usage_log(self, mock_user_profile, mock_chat_request):
        """Test that send_message creates a usage log"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock LLM service response
        with patch('app.services.chat_service.llm_service') as mock_llm_service:
            mock_llm_service.send_message = AsyncMock(return_value=(
                "Paris is the capital of France.",
                25,  # prompt_tokens
                75,  # completion_tokens
                0.003  # estimated_cost
            ))
            
            # Mock database queries for model and quota
            mock_llm_config = LLMConfiguration(
                id=uuid.uuid4(),
                model_name="gpt-3.5-turbo",
                provider="openai",
                enabled=True
            )
            
            mock_quota = DepartmentQuota(
                id=uuid.uuid4(),
                department_id=mock_user_profile.department_id,
                llm_config_id=mock_llm_config.id,
                monthly_limit_tokens=10000,
                current_usage_tokens=500
            )
            
            # Mock database operations
            mock_db.execute = AsyncMock()
            mock_db.scalar_one_or_none = AsyncMock()
            mock_db.add = Mock()
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()
            
            # Setup database query mocks
            def mock_execute_side_effect(*args, **kwargs):
                mock_result = Mock()
                mock_result.scalar_one_or_none.return_value = mock_llm_config
                mock_result.scalars.return_value.all.return_value = [mock_llm_config]
                return mock_result
            
            mock_db.execute.side_effect = mock_execute_side_effect
            
            # Mock quota check methods
            with patch.object(chat_service, '_get_default_model', return_value=mock_llm_config):
                with patch.object(chat_service, '_check_quota', return_value=None):
                    with patch.object(chat_service, '_update_quota_usage', return_value=None):
                        # Call send_message
                        response = await chat_service.send_message(
                            request=mock_chat_request,
                            user=mock_user_profile,
                            db=mock_db
                        )
                        
                        # Verify response
                        assert isinstance(response, ChatSendResponse)
                        assert response.response == "Paris is the capital of France."
                        assert response.tokens_prompt == 25
                        assert response.tokens_completion == 75
                        assert response.tokens_total == 100
                        assert response.model_used == "gpt-3.5-turbo"
                        
                        # Verify database add was called (for usage log)
                        mock_db.add.assert_called()
                        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_usage_logging_with_quota_update(self, mock_user_profile):
        """Test that usage logging properly updates quota usage"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        department_id = mock_user_profile.department_id
        llm_config_id = uuid.uuid4()
        tokens_used = 100
        
        # Mock quota object
        mock_quota = Mock()
        mock_quota.current_usage_tokens = 500
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_quota
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        
        # Call the quota update method
        await chat_service._update_quota_usage(
            db=mock_db,
            department_id=department_id,
            llm_config_id=llm_config_id,
            tokens_used=tokens_used
        )
        
        # Verify quota was updated
        assert mock_quota.current_usage_tokens == 600  # 500 + 100
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_usage_logging_error_handling(self, mock_user_profile):
        """Test error handling in usage logging"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock database error
        mock_db.add = Mock()
        mock_db.commit = AsyncMock(side_effect=Exception("Database error"))
        
        # Should raise an exception when database fails
        with pytest.raises(Exception):
            await chat_service._log_usage(
                db=mock_db,
                user_id=mock_user_profile.id,
                department_id=mock_user_profile.department_id,
                llm_config_id=uuid.uuid4(),
                prompt_tokens=50,
                completion_tokens=100,
                estimated_cost=0.005,
                request_details={},
                response_details={}
            )


class TestQuotaIntegration:
    """Test integration between usage logging and quota tracking"""
    
    @pytest.mark.asyncio
    async def test_quota_check_before_logging(self):
        """Test that quota is checked before creating usage log"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        department_id = uuid.uuid4()
        llm_config_id = uuid.uuid4()
        
        # Mock quota that would be exceeded
        mock_quota = Mock()
        mock_quota.monthly_limit_tokens = 1000
        mock_quota.current_usage_tokens = 950
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_quota
        mock_db.execute.return_value = mock_result
        
        # Should raise QuotaExceededError for large estimated usage
        with pytest.raises(QuotaExceededError):
            await chat_service._check_quota(
                db=mock_db,
                department_id=department_id,
                llm_config_id=llm_config_id,
                estimated_tokens=100  # Would exceed quota (950 + 100 > 1000)
            )
    
    @pytest.mark.asyncio
    async def test_quota_creation_if_not_exists(self):
        """Test that quota is created if it doesn't exist"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        department_id = uuid.uuid4()
        llm_config_id = uuid.uuid4()
        
        # Mock no existing quota
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        
        # Should create new quota and not raise error
        await chat_service._check_quota(
            db=mock_db,
            department_id=department_id,
            llm_config_id=llm_config_id,
            estimated_tokens=100
        )
        
        # Verify new quota was added
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the added quota has correct properties
        added_quota = mock_db.add.call_args[0][0]
        assert isinstance(added_quota, DepartmentQuota)
        assert added_quota.department_id == department_id
        assert added_quota.llm_config_id == llm_config_id
        assert added_quota.monthly_limit_tokens == 10000  # Default limit
        assert added_quota.current_usage_tokens == 0


class TestDataValidation:
    """Test data validation and integrity for usage logging"""
    
    def test_usage_log_uuid_fields(self):
        """Test that UUID fields are properly validated"""
        # Valid UUIDs should work
        valid_uuid = uuid.uuid4()
        usage_log = UsageLog(
            id=valid_uuid,
            user_id=valid_uuid,
            department_id=valid_uuid,
            llm_config_id=valid_uuid
        )
        
        assert usage_log.id == valid_uuid
        assert usage_log.user_id == valid_uuid
        assert usage_log.department_id == valid_uuid
        assert usage_log.llm_config_id == valid_uuid
    
    def test_usage_log_timestamp_validation(self):
        """Test timestamp field validation"""
        # Test with timezone-aware datetime
        tz_aware_time = datetime.now(timezone.utc)
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4(),
            timestamp=tz_aware_time
        )
        
        assert usage_log.timestamp == tz_aware_time
        
        # Test with timezone-naive datetime (should still work)
        naive_time = datetime.now()
        usage_log.timestamp = naive_time
        assert usage_log.timestamp == naive_time
    
    def test_usage_log_token_validation(self):
        """Test token count field validation"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test positive integers
        usage_log.tokens_prompt = 100
        usage_log.tokens_completion = 200
        assert usage_log.tokens_prompt == 100
        assert usage_log.tokens_completion == 200
        
        # Test zero values
        usage_log.tokens_prompt = 0
        usage_log.tokens_completion = 0
        assert usage_log.tokens_prompt == 0
        assert usage_log.tokens_completion == 0
        
        # Test large values
        usage_log.tokens_prompt = 1000000
        usage_log.tokens_completion = 2000000
        assert usage_log.tokens_prompt == 1000000
        assert usage_log.tokens_completion == 2000000
    
    def test_usage_log_cost_validation(self):
        """Test cost estimation field validation"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test decimal values
        usage_log.cost_estimated = Decimal('0.0050')
        assert usage_log.cost_estimated == Decimal('0.0050')
        
        # Test zero cost
        usage_log.cost_estimated = Decimal('0.0000')
        assert usage_log.cost_estimated == Decimal('0.0000')
        
        # Test high precision
        usage_log.cost_estimated = Decimal('0.123456789')
        assert usage_log.cost_estimated == Decimal('0.123456789')
    
    def test_usage_log_json_fields(self):
        """Test JSON field validation"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test complex JSON objects
        request_details = {
            "message": "What is AI?",
            "conversation_id": "conv-123",
            "user_message_length": 10,
            "metadata": {
                "source": "web",
                "timestamp": "2024-05-30T10:00:00Z"
            }
        }
        
        response_details = {
            "response": "AI is artificial intelligence...",
            "response_length": 35,
            "model_used": "gpt-3.5-turbo",
            "processing_time": 1.5,
            "confidence": 0.95
        }
        
        usage_log.request_details = request_details
        usage_log.response_details = response_details
        
        assert usage_log.request_details == request_details
        assert usage_log.response_details == response_details
        assert usage_log.request_details["metadata"]["source"] == "web"
        assert usage_log.response_details["processing_time"] == 1.5


class TestPerformanceAndOptimization:
    """Test performance aspects of usage logging"""
    
    @pytest.mark.asyncio
    async def test_logging_performance_impact(self):
        """Test that logging doesn't significantly impact performance"""
        import time
        
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Measure time for multiple logging operations
        start_time = time.time()
        
        for i in range(100):
            await chat_service._log_usage(
                db=mock_db,
                user_id=uuid.uuid4(),
                department_id=uuid.uuid4(),
                llm_config_id=uuid.uuid4(),
                prompt_tokens=50 + i,
                completion_tokens=100 + i,
                estimated_cost=0.005 + (i * 0.001),
                request_details={"test": f"message_{i}"},
                response_details={"test": f"response_{i}"}
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 logging operations in reasonable time (< 1 second)
        assert total_time < 1.0, f"Logging 100 operations took {total_time:.3f} seconds"
        
        # Verify all operations were called
        assert mock_db.add.call_count == 100
        assert mock_db.commit.call_count == 100
    
    def test_usage_log_memory_efficiency(self):
        """Test memory efficiency of usage log objects"""
        import sys
        
        # Create a usage log with typical data
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4(),
            tokens_prompt=150,
            tokens_completion=300,
            cost_estimated=Decimal('0.0075'),
            request_details={"message": "Test message"},
            response_details={"response": "Test response"}
        )
        
        # Check memory size (should be reasonable)
        size = sys.getsizeof(usage_log)
        
        # Usage log object should not be excessively large
        assert size < 1000, f"UsageLog object size is {size} bytes"


class TestErrorScenarios:
    """Test error handling in usage logging scenarios"""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        chat_service = ChatService()
        
        # Mock database session that fails
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.add = Mock(side_effect=Exception("Connection lost"))
        
        # Should propagate the database error
        with pytest.raises(Exception) as exc_info:
            await chat_service._log_usage(
                db=mock_db,
                user_id=uuid.uuid4(),
                department_id=uuid.uuid4(),
                llm_config_id=uuid.uuid4(),
                prompt_tokens=50,
                completion_tokens=100,
                estimated_cost=0.005,
                request_details={},
                response_details={}
            )
        
        assert "Connection lost" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_foreign_key_references(self):
        """Test handling of invalid foreign key references"""
        chat_service = ChatService()
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock integrity error for invalid foreign key
        mock_db.commit = AsyncMock(side_effect=IntegrityError(
            "Foreign key constraint failed", None, None
        ))
        mock_db.add = Mock()
        
        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            await chat_service._log_usage(
                db=mock_db,
                user_id=uuid.uuid4(),  # Assume this doesn't exist
                department_id=uuid.uuid4(),
                llm_config_id=uuid.uuid4(),
                prompt_tokens=50,
                completion_tokens=100,
                estimated_cost=0.005,
                request_details={},
                response_details={}
            )
    
    def test_invalid_token_values(self):
        """Test handling of invalid token values"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test negative values (should be handled by application logic)
        # Note: The database might allow negative values, but application should validate
        usage_log.tokens_prompt = -10
        usage_log.tokens_completion = -20
        
        # The tokens_total property should handle this gracefully
        total = usage_log.tokens_total
        assert total == -30  # -10 + -20
    
    def test_invalid_cost_values(self):
        """Test handling of invalid cost values"""
        usage_log = UsageLog(
            user_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            llm_config_id=uuid.uuid4()
        )
        
        # Test negative cost
        usage_log.cost_estimated = Decimal('-0.0050')
        assert usage_log.cost_estimated == Decimal('-0.0050')
        
        # Test extremely large cost
        usage_log.cost_estimated = Decimal('999999.9999')
        assert usage_log.cost_estimated == Decimal('999999.9999')


# Helper functions and fixtures for testing
@pytest.fixture
def sample_usage_log_data():
    """Provide sample usage log data for testing"""
    return {
        "user_id": uuid.uuid4(),
        "department_id": uuid.uuid4(),
        "llm_config_id": uuid.uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "tokens_prompt": 100,
        "tokens_completion": 200,
        "cost_estimated": Decimal('0.0050'),
        "request_details": {
            "message": "What is the weather today?",
            "conversation_id": "conv-12345",
            "user_message_length": 25
        },
        "response_details": {
            "response": "I don't have access to real-time weather data.",
            "response_length": 47,
            "model_used": "gpt-3.5-turbo",
            "processing_time": 1.2
        }
    }

@pytest.fixture
def mock_database_session():
    """Provide a mock database session for testing"""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.execute = AsyncMock()
    return mock_db

def create_mock_user_profile(
    user_id: uuid.UUID = None,
    username: str = "testuser",
    department_id: uuid.UUID = None,
    department_name: str = "IT"
) -> UserProfile:
    """Helper function to create mock user profiles"""
    return UserProfile(
        id=user_id or uuid.uuid4(),
        username=username,
        email=f"{username}@example.com",
        role="user",
        role_id=uuid.uuid4(),
        department_id=department_id or uuid.uuid4(),
        department_name=department_name,
        is_active=True
    )

def create_mock_llm_config(
    config_id: uuid.UUID = None,
    model_name: str = "gpt-3.5-turbo",
    provider: str = "openai"
) -> LLMConfiguration:
    """Helper function to create mock LLM configurations"""
    return LLMConfiguration(
        id=config_id or uuid.uuid4(),
        model_name=model_name,
        provider=provider,
        enabled=True,
        config_json={"max_tokens": 2000, "temperature": 0.7}
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
