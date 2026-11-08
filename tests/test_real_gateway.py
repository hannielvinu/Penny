import httpx
import pytest

from penny.config import Settings
from penny.policy import load_policy


@pytest.mark.real
def test_live_local_key_rejects_cloud():
    from pathlib import Path

    settings = Settings()
    key = settings.bifrost_vk_local.get_secret_value()
    if not key:
        pytest.skip("BIFROST_VK_LOCAL is not configured")
    policy = load_policy(Path.cwd())
    response = httpx.post(
        settings.bifrost_base_url + "/v1/chat/completions",
        headers={"x-bf-vk": key},
        json=dict(
            model=policy.models.cheap,
            messages=[dict(role="user", content="Reply OK")],
            max_tokens=1,
        ),
        timeout=10,
    )
    assert response.status_code == 403
    assert response.json().get("type") == "provider_blocked"
