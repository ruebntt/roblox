import asyncio
import logging
from typing import Optional, Dict
from abc import ABC, abstractmethod

from captcha_solver.captcha_api import CaptchaAPI
from captcha_solver.base import CaptchaSolverBase

logger = logging.getLogger(__name__)

class ICaptchaSolver(ABC):
    @abstractmethod
    async def solve_captcha(self, site_key: str, url: str, timeout: int = 120) -> str:
        pass

class ArkoseCaptchaSolver(CaptchaSolverBase, ICaptchaSolver):
    def __init__(self, api_client: CaptchaAPI):
        super().__init__()
        self.api_client = api_client

    async def solve_captcha(self, site_key: str, url: str, timeout: int = 120) -> str:
        try:
            task_id = await self.api_client.submit_task(site_key=site_key, url=url)
            solution = await self.api_client.get_result(task_id=task_id, timeout=timeout)
            if not solution:
                raise RuntimeError("Failed to solve CAPTCHA within timeout")
            return solution
        except Exception as e:
            logger.exception("Error solving CAPTCHA")
            raise

class CaptchaCache:
    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: str):
        async with self._lock:
            self._cache[key] = value

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            return self._cache.get(key)

captcha_solver_instance = None

def get_captcha_solver() -> ICaptchaSolver:
    global captcha_solver_instance
    if not captcha_solver_instance:
        from captcha_solver.captcha_api import CaptchaAPI
        api_client = CaptchaAPI(api_key=settings.CAPTCHA_API_KEY)
        captcha_solver_instance = ArkoseCaptchaSolver(api_client=api_client)
    return captcha_solver_instance
