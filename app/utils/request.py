"""
Request utilities for extracting client information
"""

from typing import Optional
from fastapi import Request


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP address from request headers or connection info
    Handles X-Forwarded-For header for proxied requests (Cloudflare, nginx, etc.)

    Priority:
    1. X-Forwarded-For header (first IP in list)
    2. X-Real-IP header
    3. Direct client host from connection

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address or None if unable to determine
    """
    # Check X-Forwarded-For header (Cloudflare, load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # We want the first one (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP header (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client connection
    if request.client:
        return request.client.host

    return None


def get_user_agent(request: Request) -> Optional[str]:
    """
    Extract User-Agent header from request

    Args:
        request: FastAPI Request object

    Returns:
        User-Agent string or None if not present
    """
    return request.headers.get("User-Agent")


def get_request_metadata(request: Request) -> dict:
    """
    Extract comprehensive request metadata for logging

    Args:
        request: FastAPI Request object

    Returns:
        Dictionary with IP, User-Agent, and other metadata
    """
    return {
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "method": request.method,
        "path": request.url.path,
        "referer": request.headers.get("Referer"),
        "origin": request.headers.get("Origin")
    }
