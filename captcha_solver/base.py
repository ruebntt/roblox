import abc
import asyncio
from typing import Optional, Dict, Any

class CaptchaSolverBase(abc.ABC):
    def __init__(self, api_key: str, timeout: int = 120, max_attempts: int = 3):
        self.api_key = api_key
        self.timeout = timeout
        self.max_attempts = max_attempts

    @abc.abstractmethod
    async def solve(self, site_key: str, url: str, **kwargs) -> str:
        pass

    async def _retry(self, coro, *args, **kwargs) -> str:
        last_exception: Optional[Exception] = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await asyncio.wait_for(coro(*args, **kwargs), timeout=self.timeout)
            except asyncio.TimeoutError as e:
                last_exception = e
                await asyncio.sleep(2 ** attempt * 0.5)  
            except Exception as e:
                last_exception = e
                await asyncio.sleep(1)
        raise last_exception or RuntimeError("CAPTCHA решение не удалось после нескольких попыток.")
