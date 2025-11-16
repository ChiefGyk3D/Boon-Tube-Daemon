# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Rate limiter using token bucket algorithm for API call management.
"""

import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for controlling API request rates.
    
    Enforces a maximum number of requests per time period using the token bucket algorithm.
    This prevents exceeding API rate limits by throttling requests.
    
    Example:
        # Gemini Free Tier: 15 requests per minute
        limiter = RateLimiter(max_requests=15, time_window=60.0)
        
        # Before each API call:
        limiter.acquire()  # Blocks until a token is available
        make_api_call()
    """
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds (e.g., 60.0 for per-minute limit)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = max_requests  # Start with full bucket
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = max_requests / time_window
        
        logger.info(f"⏱ Rate limiter initialized: {max_requests} requests per {time_window}s "
                   f"({self.refill_rate:.2f} req/s)")
    
    def _refill_tokens(self):
        """Refill tokens based on time elapsed since last refill."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate new tokens (never exceed max)
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.max_requests, self.tokens + new_tokens)
        self.last_refill = now
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (permission to make one API request).
        Blocks until a token is available or timeout is reached.
        
        Args:
            timeout: Maximum seconds to wait for a token (None = wait forever)
            
        Returns:
            True if token acquired, False if timeout reached
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                self._refill_tokens()
                
                if self.tokens >= 1.0:
                    # Token available - consume it
                    self.tokens -= 1.0
                    remaining = int(self.tokens)
                    logger.debug(f"🎫 Rate limit token acquired ({remaining} remaining)")
                    return True
                
                # No tokens available - check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"⏱ Rate limit timeout after {elapsed:.1f}s")
                        return False
            
            # Wait a bit before checking again
            # Calculate optimal sleep time (when next token will be available)
            wait_time = min(1.0 / self.refill_rate, 0.5)  # Max 0.5s sleep
            
            if timeout is not None:
                elapsed = time.time() - start_time
                remaining_timeout = timeout - elapsed
                wait_time = min(wait_time, remaining_timeout)
                
                if wait_time <= 0:
                    return False
            
            time.sleep(wait_time)
    
    def try_acquire(self) -> bool:
        """
        Try to acquire a token without blocking.
        
        Returns:
            True if token acquired, False if no tokens available
        """
        return self.acquire(timeout=0)
    
    def get_wait_time(self) -> float:
        """
        Get estimated wait time (in seconds) until next token is available.
        
        Returns:
            Seconds to wait, or 0 if token available now
        """
        with self.lock:
            self._refill_tokens()
            
            if self.tokens >= 1.0:
                return 0.0
            
            # Calculate time needed to refill 1 token
            tokens_needed = 1.0 - self.tokens
            return tokens_needed / self.refill_rate
    
    def reset(self):
        """Reset the rate limiter (refill all tokens)."""
        with self.lock:
            self.tokens = self.max_requests
            self.last_refill = time.time()
            logger.debug(f"🔄 Rate limiter reset ({self.max_requests} tokens available)")
