import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import httpx
import time

logger = logging.getLogger(__name__)

class BaseArkoseSolver(ABC):
    @abstractmethod
    async def solve_captcha(self, site_key: str, url: str, **kwargs) -> str:
        pass

class TwoCaptchaArkoseSolver(BaseArkoseSolver):
    def __init__(self, api_key: str, client: httpx.AsyncClient = None):
        self.api_key = api_key
        self.client = client or httpx.AsyncClient()
        self._cache: Dict[str, Dict[str, Any]] = {} 
        self._lock = asyncio.Lock()

    async def _request_solution(self, site_key: str, url: str, max_tries: int = 20, interval: int = 5) -> str:
        payload = {
            'key': self.api_key,
            'method': 'funcaptcha',
            'publickey': site_key,
            'pageurl': url,
            'json': 1
        }
        try:
            response = await self.client.post('http://2captcha.com/in.php', data=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('status') != 1:
                raise RuntimeError(f"Error from 2Captcha: {result.get('request')}")
            captcha_id = result.get('request')
        except Exception as e:
            logger.exception("Failed to submit CAPTCHA solution request")
            raise

        for attempt in range(max_tries):
            await asyncio.sleep(interval)
            try:
                res = await self.client.get(
                    'http://2captcha.com/res.php',
                    params={'key': self.api_key, 'action': 'get', 'id': captcha_id, 'json': 1},
                    timeout=10
                )
                res.raise_for_status()
                result = res.json()
                if result.get('status') == 1:
                    solution = result.get('request')
                    logger.info(f"Captcha solved: {solution}")
                    return solution
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    logger.debug(f"Captcha not ready yet, attempt {attempt + 1}")
                    continue
                else:
                    raise RuntimeError(f"Error from 2Captcha: {result.get('request')}")
            except Exception:
                logger.exception("Error polling CAPTCHA result")
        raise TimeoutError("Timeout while waiting for CAPTCHA solution")

    async def solve_captcha(self, site_key: str, url: str, **kwargs) -> str:
        cache_key = f"{site_key}:{url}"
        async with self._lock:
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached['timestamp'] < 300:  # кешировать 5 минут
                    logger.info("Returning cached CAPTCHA solution")
                    return cached['solution']

        solution = await self._request_solution(site_key, url)

        async with self._lock:
            self._cache[cache_key] = {'solution': solution, 'timestamp': time.time()}

        return solution

class ArkoseSolverFactory:
    @staticmethod
    def create_solver(config: Dict[str, Any]) -> BaseArkoseSolver:
        solver_type = config.get('type', '2captcha')
        api_key = config.get('api_key')
        if solver_type == '2captcha':
            return TwoCaptchaArkoseSolver(api_key=api_key)
        raise ValueError(f"Unknown solver type: {solver_type}")

class ArkoseSolver:
    def __init__(self, config: Dict[str, Any]):
        self.solver: BaseArkoseSolver = ArkoseSolverFactory.create_solver(config)

    async def solve(self, site_key: str, url: str, **kwargs) -> str:
        try:
            solution = await self.solver.solve_captcha(site_key, url, **kwargs)
            return solution
        except Exception as e:
            logger.exception("Failed to solve CAPTCHA")
            raise
