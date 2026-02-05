import pytest
from captcha_solver.captcha_api import CaptchaAPI
from captcha_solver.arkose_solver import ArkoseSolver
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_captcha_api():
    api = AsyncMock(spec=CaptchaAPI)
    api.solve_captcha.return_value = "mocked_captcha_token"
    return api

@pytest.fixture
def arkose_solver_instance(mock_captcha_api):
    return ArkoseSolver(captcha_api=mock_captcha_api)

@pytest.mark.asyncio
async def test_solve_arkose_captcha_success(arkose_solver_instance, mock_captcha_api):
    result = await arkose_solver_instance.solve("some_captcha_data")
    assert result == "mocked_captcha_token"
    mock_captcha_api.solve_captcha.assert_awaited_once()

@pytest.mark.asyncio
async def test_solve_arkose_captcha_failure(arkose_solver_instance, mock_captcha_api):
    mock_captcha_api.solve_captcha.side_effect = Exception("API error")
    with pytest.raises(Exception) as e:
        await arkose_solver_instance.solve("some_captcha_data")
    assert "API error" in str(e.value)

@pytest.mark.asyncio
async def test_captcha_api_integration( ):
    api = CaptchaAPI(api_key="test_key")
    token = await api.solve_captcha("test_captcha_data")
    assert isinstance(token, str)
    assert len(token) > 0
