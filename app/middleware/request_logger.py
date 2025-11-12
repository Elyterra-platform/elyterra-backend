"""
API Request Logging Middleware
Logs all API requests for legal compliance, audit trail, and analytics
"""

import time
from fastapi import Request
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.api_request_log import ApiRequestLog
from app.utils.request import get_client_ip, get_user_agent
from app.core.security import decode_token


async def log_api_request(request: Request, call_next):
    """
    Middleware to log all API requests

    Logs:
    - User ID (from JWT token)
    - Endpoint path
    - HTTP method
    - IP address (with proxy support)
    - User-Agent string
    - HTTP status code
    - Request duration in milliseconds
    - Timestamp

    Retention: ≥12 months for legal compliance
    """
    # Extract user ID from JWT token (if authenticated)
    user_id = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        try:
            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub")  # User ID from token
        except Exception:
            pass  # Token invalid or expired, log as anonymous

    # Extract request metadata
    endpoint = request.url.path
    method = request.method
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Measure request duration
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Log to database (async background task to avoid blocking response)
    try:
        db = SessionLocal()
        try:
            log_entry = ApiRequestLog(
                user_id=int(user_id) if user_id else None,
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=response.status_code,
                request_duration_ms=duration_ms
            )
            db.add(log_entry)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        # Log error but don't fail the request
        print(f"Warning: Failed to log API request: {e}")

    return response
