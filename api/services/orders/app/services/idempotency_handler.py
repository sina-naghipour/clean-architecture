import hashlib
import time
from typing import Set

class IdempotencyHandler:
    def __init__(self):
        self._processed_keys: Set[str] = set()

    def generate_key(self, user_id: str, items: list) -> str:
        items_hash = hashlib.md5(str(items).encode()).hexdigest()[:8]
        return f"{user_id}_{items_hash}_{int(time.time())}"

    def is_duplicate(self, key: str) -> bool:
        return key in self._processed_keys

    def store_key(self, key: str):
        self._processed_keys.add(key)