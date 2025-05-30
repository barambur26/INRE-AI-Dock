"""
Rate Limiting Middleware for AI Dock App Authentication Endpoints

This module provides comprehensive rate limiting for authentication endpoints
to prevent brute force attacks and abuse.

Features:
- IP-based rate limiting
- User-based rate limiting
- Different limits for different endpoints
- Admin exemptions
- Detailed logging and monitoring
"""

import time
import logging
from typing import Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
class InMemoryStorage:
    """In-memory storage for rate limiting (development only)"""
    def __init__(self):
        self.data: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.user_attempts: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        
    def add_attempt(self, key: str, endpoint: str = "general") -> None:
        """Add an attempt to the rate limit counter"""
        now = time.time()
        window = self._get_window_for_endpoint(endpoint)
        
        # Clean old entries
        while self.data[key] and now - self.data[key][0] > window:
            self.data[key].popleft()
            
        self.data[key].append(now)
        
    def get_attempts(self, key: str, endpoint: str = "general") -> int:
        """Get number of attempts in current window"""
        now = time.time()
        window = self._get_window_for_endpoint(endpoint)
        
        # Clean old entries
        while self.data[key] and now - self.data[key][0] > window:
            self.data[key].popleft()
            
        return len(self.data[key])
    
    def add_user_attempt(self, username: str, ip: str, endpoint: str = "login") -> None:
        """Add user-specific attempt"""
        key = f"{username}:{ip}"
        now = time.time()
        window = self._get_window_for_endpoint(endpoint)
        
        # Clean old entries
        while self.user_attempts[username][key] and now - self.user_attempts[username][key][0] > window:
            self.user_attempts[username][key].popleft()
            
        self.user_attempts[username][key].append(now)
        
    def get_user_attempts(self, username: str, ip: str, endpoint: str = "login") -> int:
        """Get user-specific attempts"""
        key = f"{username}:{ip}"
        now = time.time()
        window = self._get_window_for_endpoint(endpoint)
        
        # Clean old entries  
        while self.user_attempts[username][key] and now - self.user_attempts[username][key][0] > window:
            self.user_attempts[username][key].popleft()
            
        return len(self.user_attempts[username][key])
    
    def block_ip(self, ip: str, duration_minutes: int = 15) -> None:
        """Block an IP address for specified duration"""
        self.blocked_ips[ip] = datetime.utcnow() + timedelta(minutes=duration_minutes)
        logger.warning(f"IP {ip} blocked for {duration_minutes} minutes due to rate limiting")
        
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is currently blocked"""
        if ip in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[ip]:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[ip]
        return False
    
    def _get_window_for_endpoint(self, endpoint: str) -> int:
        """Get time window in seconds for endpoint"""
        windows = {
            "login": 900,      # 15 minutes
            "refresh": 300,    # 5 minutes  
            "logout": 60,      # 1 minute
            "general": 300,    # 5 minutes default
        }
        return windows.get(endpoint, 300)

# Global storage instance
rate_limit_storage = InMemoryStorage()

# Rate limiting configurations
RATE_LIMITS = {
    "login": {
        "requests": 5,      # 5 attempts per 15 minutes per IP
        "window": 900,      # 15 minutes
        "user_limit": 3,    # 3 attempts per user per 15 minutes
        "block_threshold": 10,  # Block IP after 10 attempts
        "block_duration": 30,   # Block for 30 minutes
    },
    "refresh": {
        "requests": 30,     # 30 refresh attempts per 5 minutes per IP
        "window": 300,      # 5 minutes
        "user_limit": 20,   # 20 attempts per user per 5 minutes
        "block_threshold": 50,
        "block_duration": 15,
    },
    "logout": {
        "requests": 10,     # 10 logout attempts per minute per IP
        "window": 60,       # 1 minute
        "user_limit": 5,    # 5 attempts per user per minute
        "block_threshold": 20,
        "block_duration": 5,
    },
    "profile": {
        "requests": 60,     # 60 profile requests per 5 minutes per IP
        "window": 300,      # 5 minutes
        "user_limit": 40,   # 40 attempts per user per 5 minutes
        "block_threshold": 100,
        "block_duration": 10,
    },
    "general": {
        "requests": 100,    # 100 requests per 5 minutes per IP
        "window": 300,      # 5 minutes
        "user_limit": 60,   # 60 attempts per user per 5 minutes
        "block_threshold": 200,
        "block_duration": 15,
    }
}

def get_client_ip(request: Request) -> str:
    """Extract client IP from request with proxy support"""
    # Check for forwarded IP headers (common with proxies/load balancers)
    forwarded_ips = [
        request.headers.get("x-forwarded-for"),
        request.headers.get("x-real-ip"),
        request.headers.get("cf-connecting-ip"),  # Cloudflare
        request.headers.get("x-client-ip"),
    ]
    
    for ip_header in forwarded_ips:
        if ip_header:
            # Take the first IP if multiple are present
            ip = ip_header.split(",")[0].strip()
            if ip and ip != "unknown":
                return ip
    
    # Fall back to direct connection IP
    return get_remote_address(request)

def get_endpoint_type(path: str) -> str:
    """Determine endpoint type from request path"""
    if "/auth/login" in path:
        return "login"
    elif "/auth/refresh" in path:
        return "refresh"
    elif "/auth/logout" in path:
        return "logout"
    elif "/auth/me" in path:
        return "profile"
    elif "/auth/" in path:
        return "general"
    else:
        return "general"

def extract_username_from_request(request: Request) -> Optional[str]:
    """Extract username from request body or headers"""
    try:
        # For login requests, username might be in the request body
        if hasattr(request.state, 'username'):
            return request.state.username
        
        # Could also extract from Authorization header for authenticated requests
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would require decoding the JWT token
            # For now, we'll handle this in the middleware
            pass
            
    except Exception as e:
        logger.debug(f"Could not extract username from request: {e}")
    
    return None

def is_admin_user(request: Request) -> bool:
    """Check if the current user is an admin (exempt from rate limiting)"""
    try:
        # This would check the JWT token for admin role
        # For now, we'll implement a simple check
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a full implementation, decode JWT and check role
            # For now, return False to apply rate limiting to all users
            pass
    except Exception as e:
        logger.debug(f"Could not check admin status: {e}")
    
    return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware for authentication endpoints
    """
    
    def __init__(self, app, enable_rate_limiting: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        
        # Skip rate limiting if disabled (for testing)
        if not self.enable_rate_limiting:
            return await call_next(request)
            
        # Skip rate limiting for non-auth endpoints
        if not request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)
            
        # Get client information
        client_ip = get_client_ip(request)
        endpoint_type = get_endpoint_type(request.url.path)
        
        # Check if IP is blocked
        if rate_limit_storage.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP {client_ip} attempted access to {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "IP address temporarily blocked due to rate limiting. Please try again later.",
                    "error_code": "IP_BLOCKED",
                    "retry_after": 900  # seconds
                }
            )
        
        # Skip rate limiting for admin users (if authenticated)
        if is_admin_user(request):
            logger.debug(f"Admin user from {client_ip} - rate limiting skipped")
            return await call_next(request)
        
        # Apply rate limiting
        try:
            await self._apply_rate_limiting(request, client_ip, endpoint_type)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        
        # Process the request
        response = await call_next(request)
        
        # Log successful authentication attempts
        if response.status_code == 200 and endpoint_type in ["login", "refresh"]:
            logger.info(f"Successful {endpoint_type} from {client_ip} for endpoint {request.url.path}")
        
        return response
    
    async def _apply_rate_limiting(self, request: Request, client_ip: str, endpoint_type: str):
        """Apply rate limiting logic"""
        
        limits = RATE_LIMITS.get(endpoint_type, RATE_LIMITS["general"])
        
        # Add attempt to counter
        rate_limit_storage.add_attempt(client_ip, endpoint_type)
        
        # Check IP-based limits
        ip_attempts = rate_limit_storage.get_attempts(client_ip, endpoint_type)
        
        if ip_attempts > limits["requests"]:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on {endpoint_type}: "
                f"{ip_attempts} attempts in {limits['window']} seconds"
            )
            
            # Check if we should block the IP
            if ip_attempts >= limits["block_threshold"]:
                rate_limit_storage.block_ip(client_ip, limits["block_duration"])
                
            raise HTTPException(
                status_code=429,
                detail={
                    "message": f"Rate limit exceeded for {endpoint_type}",
                    "attempts": ip_attempts,
                    "limit": limits["requests"],
                    "window_seconds": limits["window"],
                    "retry_after": limits["window"],
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            )
        
        # For login attempts, also check user-based limits
        if endpoint_type == "login":
            await self._check_user_rate_limit(request, client_ip, limits)
    
    async def _check_user_rate_limit(self, request: Request, client_ip: str, limits: dict):
        """Check user-specific rate limits for login attempts"""
        
        # Extract username from request
        # This is tricky since we need to read the request body
        try:
            if request.method == "POST":
                # Store original body
                body = await request.body()
                
                # Try to extract username (this is a simplified approach)
                if body:
                    import json
                    try:
                        body_data = json.loads(body.decode())
                        username = body_data.get("username")
                        
                        if username:
                            rate_limit_storage.add_user_attempt(username, client_ip, "login")
                            user_attempts = rate_limit_storage.get_user_attempts(username, client_ip, "login")
                            
                            if user_attempts > limits["user_limit"]:
                                logger.warning(
                                    f"User rate limit exceeded for {username} from {client_ip}: "
                                    f"{user_attempts} attempts"
                                )
                                
                                raise HTTPException(
                                    status_code=429,
                                    detail={
                                        "message": "Too many login attempts for this user",
                                        "attempts": user_attempts,
                                        "limit": limits["user_limit"],
                                        "window_seconds": limits["window"],
                                        "retry_after": limits["window"],
                                        "error_code": "USER_RATE_LIMIT_EXCEEDED"
                                    }
                                )
                                
                    except json.JSONDecodeError:
                        pass  # Invalid JSON, let the endpoint handle it
                        
        except Exception as e:
            logger.debug(f"Could not check user rate limit: {e}")
            # Don't fail the request if we can't check user limits

# Limiter instance for decorator-based rate limiting
limiter = Limiter(key_func=get_remote_address)

# Rate limit exceeded handler
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    response = JSONResponse(
        status_code=429,
        content={
            "detail": {
                "message": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": exc.retry_after
            }
        }
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    return response

# Utility functions for monitoring
def get_rate_limit_stats() -> Dict:
    """Get current rate limiting statistics"""
    return {
        "blocked_ips": len(rate_limit_storage.blocked_ips),
        "active_limits": len(rate_limit_storage.data),
        "user_attempts": len(rate_limit_storage.user_attempts),
        "blocked_ip_list": [
            {
                "ip": ip,
                "blocked_until": blocked_until.isoformat(),
                "remaining_seconds": max(0, (blocked_until - datetime.utcnow()).total_seconds())
            }
            for ip, blocked_until in rate_limit_storage.blocked_ips.items()
        ]
    }

def clear_rate_limits(ip: str = None) -> Dict:
    """Clear rate limits (admin function)"""
    if ip:
        # Clear specific IP
        if ip in rate_limit_storage.data:
            del rate_limit_storage.data[ip]
        if ip in rate_limit_storage.blocked_ips:
            del rate_limit_storage.blocked_ips[ip]
        return {"message": f"Rate limits cleared for IP {ip}"}
    else:
        # Clear all rate limits
        rate_limit_storage.data.clear()
        rate_limit_storage.blocked_ips.clear()
        rate_limit_storage.user_attempts.clear()
        return {"message": "All rate limits cleared"}
