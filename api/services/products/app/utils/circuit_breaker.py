import time
from enum import Enum
import logging


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=30.0, half_open_max_requests=3, logger=None):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_requests = half_open_max_requests
        self.logger = logger or logging.getLogger(__name__)
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_attempts = 0
        
    def can_execute(self):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_attempts = 0
                self.logger.info("Circuit breaker moved from OPEN to HALF_OPEN")
                return True
            self.logger.warning("Circuit breaker is OPEN, rejecting request")
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_attempts >= self.half_open_max_requests:
                self.logger.warning("Circuit breaker HALF_OPEN limit reached")
                return False
            self.half_open_attempts += 1
            self.logger.debug(f"HALF_OPEN attempt {self.half_open_attempts}/{self.half_open_max_requests}")
            return True
        
        return True
    
    def on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_attempts = 0
            self.logger.info("Circuit breaker moved from HALF_OPEN to CLOSED")
        else:
            self.failure_count = 0
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.error(f"Circuit breaker moved from HALF_OPEN to OPEN after failure")
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.logger.error(f"Circuit breaker moved from CLOSED to OPEN after {self.failure_count} failures")
        else:
            self.logger.warning(f"Circuit failure count: {self.failure_count}/{self.failure_threshold}")
    
    def get_state(self):
        return self.state