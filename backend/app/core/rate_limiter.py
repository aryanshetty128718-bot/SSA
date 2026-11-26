import time
from typing import Dict, List
from fastapi import Request
from app.core.exceptions import AuthenticationError

class InMemoryRateLimiter:
    """Simple sliding-window rate limiter for brute-force protection."""
    def __init__(self, requests_limit: int = 5, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.ip_records: Dict[str, List[float]] = {}

    def check_rate_limit(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        timestamps = self.ip_records.get(client_ip, [])
        # Filter timestamps within current window
        valid_timestamps = [ts for ts in timestamps if ts > window_start]

        if len(valid_timestamps) >= self.requests_limit:
            raise AuthenticationError("Too many login attempts. Please try again after 60 seconds.")

        valid_timestamps.append(now)
        self.ip_records[client_ip] = valid_timestamps

    def reset(self):
        """Reset rate limiter state (useful for test isolation)."""
        self.ip_records.clear()

login_rate_limiter = InMemoryRateLimiter(requests_limit=5, window_seconds=60)
