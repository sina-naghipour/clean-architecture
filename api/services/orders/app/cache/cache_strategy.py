from typing import Dict, Optional
import logging
import os
from dotenv import load_dotenv

load_dotenv()


class CacheStrategy:
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    
    def should_cache_order(self, order_data: Dict) -> bool:
        if not self.enabled:
            return False
        
        status = order_data.get('status', '')
        total = order_data.get('total', 0)
        
        if status in ['failed', 'canceled']:
            return False
        
        if total > 10000:
            return True
        
        return True
    
    def get_order_ttl(self, order_data: Dict) -> int:
        status = order_data.get('status', '')
        
        if status == 'pending':
            return 60
        
        if status == 'paid':
            return 1800
        
        return 300
    
    def should_cache_user_orders(self, user_id: str) -> bool:
        if not self.enabled:
            return False
        
        return True

cache_strategy = CacheStrategy()