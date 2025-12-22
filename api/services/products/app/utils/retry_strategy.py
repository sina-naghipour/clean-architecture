import asyncio
import random
import logging


class RetryStrategy:
    def __init__(self, max_retries=3, initial_backoff=0.1, max_backoff=2.0, backoff_factor=2.0, logger=None):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute_with_retry(self, operation, *args, **kwargs):
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"Retry attempt {attempt}/{self.max_retries}")
                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt} failed: {str(e)}")
                if attempt == self.max_retries:
                    break
                
                backoff = self._calculate_backoff(attempt)
                self.logger.debug(f"Waiting {backoff:.2f}s before retry")
                await asyncio.sleep(backoff)
        
        self.logger.error(f"All {self.max_retries} retry attempts failed")
        raise last_exception if last_exception else RuntimeError("Operation failed")
    
    def _calculate_backoff(self, attempt):
        backoff = min(
            self.initial_backoff * (self.backoff_factor ** attempt),
            self.max_backoff
        )
        jitter_factor = random.uniform(0.9, 1.1)
        return backoff * jitter_factor