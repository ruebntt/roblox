import hashlib
import hmac
import json
import time
import asyncio
from typing import Dict, Any

def generate_secure_token(secret_key: str, data: Dict[str, Any]) -> str:
    serialized_data = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return hmac.new(secret_key.encode(), serialized_data.encode(), hashlib.sha256).hexdigest()

def get_current_timestamp() -> int:
    return int(time.time())

def hash_site_key(site_key: str, salt: str) -> str:
    return hashlib.sha256(f"{site_key}{salt}".encode()).hexdigest()

async def exponential_backoff(retries: int, base_delay: float = 0.5, max_delay: float = 10.0):
    for attempt in range(retries):
        delay = min(base_delay * (2 ** attempt), max_delay)
        await asyncio.sleep(delay)
