"""
Background Tasks for AI Dock App

This module contains Celery tasks for background processing including:
- Token cleanup (expired/revoked tokens)
- Usage log cleanup
- Security monitoring
- System maintenance tasks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text

from ..core.config import settings
from ..core.database import get_db_session
from ..models.refresh_token import RefreshToken
from ..models.user import User

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "ai_dock_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.cleanup"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Run token cleanup every hour
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup.cleanup_expired_tokens",
            "schedule": 3600.0,  # 1 hour in seconds
        },
        # Run security monitoring every 15 minutes
        "security-monitoring": {
            "task": "app.tasks.cleanup.security_monitoring_task",
            "schedule": 900.0,  # 15 minutes in seconds
        },
        # Run database maintenance daily at 2 AM
        "database-maintenance": {
            "task": "app.tasks.cleanup.database_maintenance_task",
            "schedule": {
                "minute": 0,
                "hour": 2
            },
        },
    },
)

@celery_app.task(bind=True, name="app.tasks.cleanup.cleanup_expired_tokens")
def cleanup_expired_tokens(self) -> Dict:
    """
    Cleanup expired and revoked refresh tokens
    
    This task removes:
    1. Tokens that have passed their expiration date
    2. Tokens that have been explicitly revoked
    3. Tokens older than max retention period (configurable)
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        logger.info("Starting token cleanup task")
        
        with get_db_session() as db:
            current_time = datetime.utcnow()
            
            # Define cleanup criteria
            max_retention_days = getattr(settings, 'TOKEN_MAX_RETENTION_DAYS', 90)
            retention_cutoff = current_time - timedelta(days=max_retention_days)
            
            # Count tokens before cleanup
            total_tokens_before = db.query(RefreshToken).count()
            
            # Find expired tokens
            expired_tokens = db.query(RefreshToken).filter(
                RefreshToken.expires_at < current_time
            ).all()
            
            # Find revoked tokens
            revoked_tokens = db.query(RefreshToken).filter(
                RefreshToken.is_revoked == True
            ).all()
            
            # Find tokens older than retention period
            old_tokens = db.query(RefreshToken).filter(
                RefreshToken.created_at < retention_cutoff
            ).all()
            
            # Combine all tokens to delete (remove duplicates)
            tokens_to_delete = set()
            tokens_to_delete.update(expired_tokens)
            tokens_to_delete.update(revoked_tokens)
            tokens_to_delete.update(old_tokens)
            
            # Delete tokens
            deleted_count = 0
            expired_count = len(expired_tokens)
            revoked_count = len(revoked_tokens)
            old_count = len(old_tokens)
            
            for token in tokens_to_delete:
                try:
                    db.delete(token)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting token {token.id}: {e}")
            
            # Commit changes
            db.commit()
            
            # Count tokens after cleanup
            total_tokens_after = db.query(RefreshToken).count()
            
            result = {
                "status": "success",
                "timestamp": current_time.isoformat(),
                "tokens_before": total_tokens_before,
                "tokens_after": total_tokens_after,
                "tokens_deleted": deleted_count,
                "breakdown": {
                    "expired": expired_count,
                    "revoked": revoked_count,
                    "old_retention": old_count,
                },
                "retention_days": max_retention_days,
            }
            
            logger.info(
                f"Token cleanup completed: {deleted_count} tokens deleted "
                f"({expired_count} expired, {revoked_count} revoked, {old_count} old)"
            )
            
            return result
            
    except Exception as e:
        error_msg = f"Token cleanup task failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "timestamp": datetime.utcnow().isoformat()}
        )
        
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True, name="app.tasks.cleanup.cleanup_user_sessions")
def cleanup_user_sessions(self, user_id: str) -> Dict:
    """
    Cleanup all sessions for a specific user
    
    Used when:
    - User requests to logout from all devices
    - Admin forces user logout
    - User account is deactivated
    
    Args:
        user_id: UUID of the user
        
    Returns:
        Dict with cleanup results
    """
    try:
        logger.info(f"Starting session cleanup for user {user_id}")
        
        with get_db_session() as db:
            # Find all active tokens for the user
            user_tokens = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            ).all()
            
            # Revoke all tokens
            revoked_count = 0
            for token in user_tokens:
                token.is_revoked = True
                token.revoked_at = datetime.utcnow()
                revoked_count += 1
            
            db.commit()
            
            result = {
                "status": "success",
                "user_id": user_id,
                "tokens_revoked": revoked_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Session cleanup completed for user {user_id}: {revoked_count} tokens revoked")
            return result
            
    except Exception as e:
        error_msg = f"Session cleanup failed for user {user_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "user_id": user_id, "timestamp": datetime.utcnow().isoformat()}
        )
        
        return {
            "status": "error",
            "error": error_msg,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True, name="app.tasks.cleanup.security_monitoring_task")
def security_monitoring_task(self) -> Dict:
    """
    Security monitoring and alerting task
    
    Monitors for:
    - Unusual login patterns
    - High rate limiting incidents  
    - Suspicious token usage
    - Failed authentication attempts
    
    Returns:
        Dict with security monitoring results
    """
    try:
        logger.info("Starting security monitoring task")
        
        with get_db_session() as db:
            current_time = datetime.utcnow()
            check_period = current_time - timedelta(minutes=15)  # Last 15 minutes
            
            # Check for suspicious patterns
            alerts = []
            
            # 1. Check for users with excessive failed logins
            # (This would require login attempt logging - placeholder for now)
            
            # 2. Check for tokens created and immediately revoked (suspicious)
            suspicious_tokens = db.query(RefreshToken).filter(
                RefreshToken.created_at > check_period,
                RefreshToken.is_revoked == True,
                RefreshToken.revoked_at - RefreshToken.created_at < timedelta(minutes=1)
            ).count()
            
            if suspicious_tokens > 10:
                alerts.append({
                    "type": "suspicious_token_pattern",
                    "count": suspicious_tokens,
                    "description": "High number of tokens created and immediately revoked"
                })
            
            # 3. Check for inactive users with new tokens
            inactive_user_tokens = db.query(RefreshToken).join(User).filter(
                RefreshToken.created_at > check_period,
                User.is_active == False
            ).count()
            
            if inactive_user_tokens > 0:
                alerts.append({
                    "type": "inactive_user_tokens",
                    "count": inactive_user_tokens,
                    "description": "New tokens created for inactive users"
                })
            
            # 4. Check for tokens with unusual characteristics
            old_tokens_still_active = db.query(RefreshToken).filter(
                RefreshToken.created_at < current_time - timedelta(days=30),
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > current_time
            ).count()
            
            if old_tokens_still_active > 100:
                alerts.append({
                    "type": "old_active_tokens",
                    "count": old_tokens_still_active,
                    "description": "High number of old tokens still active"
                })
            
            result = {
                "status": "success",
                "timestamp": current_time.isoformat(),
                "check_period_start": check_period.isoformat(),
                "alerts": alerts,
                "metrics": {
                    "total_active_tokens": db.query(RefreshToken).filter(
                        RefreshToken.is_revoked == False,
                        RefreshToken.expires_at > current_time
                    ).count(),
                    "tokens_created_last_hour": db.query(RefreshToken).filter(
                        RefreshToken.created_at > current_time - timedelta(hours=1)
                    ).count(),
                    "tokens_revoked_last_hour": db.query(RefreshToken).filter(
                        RefreshToken.revoked_at > current_time - timedelta(hours=1)
                    ).count(),
                }
            }
            
            # Log alerts
            if alerts:
                logger.warning(f"Security monitoring found {len(alerts)} alerts: {alerts}")
            else:
                logger.info("Security monitoring completed - no alerts")
                
            return result
            
    except Exception as e:
        error_msg = f"Security monitoring task failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "timestamp": datetime.utcnow().isoformat()}
        )
        
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True, name="app.tasks.cleanup.database_maintenance_task")
def database_maintenance_task(self) -> Dict:
    """
    Database maintenance and optimization task
    
    Performs:
    - Database statistics update
    - Index optimization
    - Dead row cleaning
    - Performance monitoring
    
    Returns:
        Dict with maintenance results
    """
    try:
        logger.info("Starting database maintenance task")
        
        with get_db_session() as db:
            current_time = datetime.utcnow()
            
            # Basic database statistics
            stats = {
                "total_users": db.query(User).count(),
                "active_users": db.query(User).filter(User.is_active == True).count(),
                "total_tokens": db.query(RefreshToken).count(),
                "active_tokens": db.query(RefreshToken).filter(
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > current_time
                ).count(),
                "expired_tokens": db.query(RefreshToken).filter(
                    RefreshToken.expires_at < current_time
                ).count(),
                "revoked_tokens": db.query(RefreshToken).filter(
                    RefreshToken.is_revoked == True
                ).count(),
            }
            
            # Database maintenance recommendations
            recommendations = []
            
            if stats["expired_tokens"] > 1000:
                recommendations.append({
                    "type": "cleanup_required",
                    "message": f"{stats['expired_tokens']} expired tokens should be cleaned up"
                })
            
            if stats["revoked_tokens"] > 500:
                recommendations.append({
                    "type": "cleanup_required", 
                    "message": f"{stats['revoked_tokens']} revoked tokens should be cleaned up"
                })
            
            # Calculate token usage patterns
            token_age_stats = db.execute(text("""
                SELECT 
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(revoked_at, expires_at) - created_at))) as avg_lifetime_seconds
                FROM refresh_tokens 
                WHERE created_at > :cutoff
            """), {"cutoff": current_time - timedelta(days=7)}).fetchone()
            
            result = {
                "status": "success",
                "timestamp": current_time.isoformat(),
                "database_stats": stats,
                "recommendations": recommendations,
                "token_usage_patterns": {
                    "weekly_tokens": token_age_stats.count if token_age_stats else 0,
                    "avg_token_lifetime_hours": round((token_age_stats.avg_lifetime_seconds or 0) / 3600, 2) if token_age_stats else 0,
                }
            }
            
            logger.info(f"Database maintenance completed: {stats}")
            return result
            
    except Exception as e:
        error_msg = f"Database maintenance task failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        self.update_state(
            state="FAILURE",
            meta={"error": error_msg, "timestamp": datetime.utcnow().isoformat()}
        )
        
        return {
            "status": "error",
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        }

# Utility functions for manual task execution
def trigger_token_cleanup() -> str:
    """Manually trigger token cleanup task"""
    task = cleanup_expired_tokens.delay()
    return task.id

def trigger_user_session_cleanup(user_id: str) -> str:
    """Manually trigger user session cleanup"""
    task = cleanup_user_sessions.delay(user_id)
    return task.id

def get_task_result(task_id: str) -> Dict:
    """Get result of a background task"""
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }

def get_task_info() -> Dict:
    """Get information about registered tasks and their schedules"""
    return {
        "registered_tasks": list(celery_app.tasks.keys()),
        "beat_schedule": celery_app.conf.beat_schedule,
        "active_tasks": len(celery_app.control.inspect().active() or {}),
    }
