import time

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_until = 0

    def is_open(self) -> bool:
        if self.circuit_open:
            if time.time() < self.circuit_open_until:
                return True
            self.circuit_open = False
            self.failure_count = 0
        return False

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_open_until = time.time() + self.reset_timeout

    def record_success(self):
        self.failure_count = 0
        self.circuit_open = False