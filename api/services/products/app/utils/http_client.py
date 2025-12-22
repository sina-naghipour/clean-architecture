import httpx
from typing import Optional, Dict, Any, Callable
import json
import logging

from .circuit_breaker import CircuitBreaker
from .retry_strategy import RetryStrategy
from .resilience_config import ResilienceConfig


class ResilientHttpClient:
    def __init__(self, config: ResilienceConfig, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        self.client = httpx.AsyncClient(timeout=config.timeout)
        
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker.failure_threshold,
            reset_timeout=config.circuit_breaker.reset_timeout,
            half_open_max_requests=config.circuit_breaker.half_open_max_requests,
            logger=self.logger
        )
        
        self.retry_strategy = RetryStrategy(
            max_retries=config.retry.max_retries,
            initial_backoff=config.retry.initial_backoff,
            max_backoff=config.retry.max_backoff,
            backoff_factor=config.retry.backoff_factor,
            logger=self.logger
        )
    
    async def close(self):
        try:
            await self.client.aclose()
        except Exception as e:
            self.logger.error(f"Error closing HTTP client: {str(e)}")
    
    async def _execute_with_resilience(self, operation: Callable, *args, **kwargs):
        if not self.circuit_breaker.can_execute():
            error_msg = "Circuit breaker is open, request rejected"
            self.logger.error(error_msg)
            raise httpx.RequestError(error_msg)
        
        try:
            result = await self.retry_strategy.execute_with_retry(
                operation, *args, **kwargs
            )
            self.circuit_breaker.on_success()
            self.logger.debug("Request succeeded")
            return result
        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            self.circuit_breaker.on_failure()
            raise
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.logger.debug(f"GET {url}")
        async def _get():
            return await self.client.get(url, headers=headers)
        return await self._execute_with_resilience(_get)
    
    async def post(self, url: str, data: Any = None, files=None, params=None, headers: Optional[Dict[str, str]] = None):
        self.logger.debug(f"POST {url}")
        async def _post():
            return await self.client.post(url, data=data, files=files, params=params, headers=headers)
        return await self._execute_with_resilience(_post)
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None):
        self.logger.debug(f"DELETE {url}")
        async def _delete():
            return await self.client.delete(url, headers=headers)
        return await self._execute_with_resilience(_delete)
    
    def get_circuit_state(self):
        return self.circuit_breaker.get_state()