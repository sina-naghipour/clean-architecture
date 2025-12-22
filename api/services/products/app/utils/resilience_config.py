from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_backoff: float = 0.1
    max_backoff: float = 2.0
    backoff_factor: float = 2.0


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    reset_timeout: float = 30.0
    half_open_max_requests: int = 3


@dataclass
class ResilienceConfig:
    retry: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    timeout: float = 30.0