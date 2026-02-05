import asyncio
import aiohttp
from typing import Dict, Any, Optional

class CaptchaAPI:
    def __init__(self, api_key: str, service: str = '2captcha'):
        self.api_key = api_key
        self.service = service
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = 'https://2captcha.com/p/funcaptcha' if service == '2captcha' else 'https://2captcha.com/p/funcaptcha'

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def create_task(self, payload: Dict[str, Any]) -> str:
        session = await self._get_session()
        url = f"{self.base_url}/in.php"
        async with session.post(url, data=payload) as response:
            resp_text = await response.text()
            if resp_text.startswith('OK|'):
                return resp_text.split('|')[1]
            else:
                raise RuntimeError(f"Ошибка при создании задачи: {resp_text}")

    async def get_result(self, task_id: str) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}/res.php"
        params = {'id': task_id, 'action': 'get'}
        async with session.get(url, params=params) as response:
            resp_text = await response.text()
            if resp_text.startswith('OK|'):
                result = resp_text.split('|')[1]
                return {'status': 'ready', 'solution': result}
            elif 'CAPCHA_NOT_READY' in resp_text:
                return {'status': 'pending'}
            else:
                raise RuntimeError(f"Ошибка получения результата: {resp_text}")

    async def close(self):
        if self.session:
            await self.session.close()
