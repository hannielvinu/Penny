"""Create budgeted, provider-restricted virtual keys through the documented API.

Run --prepare once before Compose; no key values are written to tracked files.
Prints newly-created inference key values intentionally: keep stdout private.
"""

import argparse
import os
import secrets
from pathlib import Path

import httpx
from dotenv import load_dotenv


def prepare_env(root: Path):
    target = root / ".env"
    if target.exists():
        raise ValueError(".env already exists; set BIFROST_SETUP_TOKEN manually if missing")
    text = (root / ".env.example").read_text(encoding="utf-8")
    text += (
        "\n# First-admin setup lock; keep private.\nBIFROST_SETUP_TOKEN="
        + secrets.token_urlsafe(32)
        + "\n"
    )
    target.write_text(text, encoding="utf-8")
    target.chmod(0o600)
    print("Created untracked .env with a setup token. Fill provider keys, then make up.")


def bootstrap(base_url: str, headers: dict, client=None):
    owned = client is None
    client = client or httpx.Client(base_url=base_url, timeout=20, headers=headers)
    try:
        response = client.get("/api/governance/virtual-keys")
        response.raise_for_status()
        data = response.json()
        existing = (data.get("virtual_keys") or []) if isinstance(data, dict) else (data or [])
        names = {v["name"] for v in existing}
        configs = [
            ("penny-dev", ["openai", "anthropic"], 0.5, "BIFROST_VK_DEV"),
            ("penny-local", ["ollama"], None, "BIFROST_VK_LOCAL"),
            ("penny-demo-tiny", ["openai", "anthropic"], 0.001, "BIFROST_VK_DEMO_TINY"),
        ]
        for name, providers, budget, variable in configs:
            if name in names:
                print(
                    f"{name} already exists; unchanged. Retrieve its value privately in the gateway dashboard."
                )
                continue
            payload = dict(
                name=name,
                is_active=True,
                disable_content_logging=True,
                provider_configs=[
                    dict(provider=p, weight=1, allowed_models=["*"], key_ids=["*"])
                    for p in providers
                ],
                rate_limit=dict(
                    token_max_limit=150000,
                    token_reset_duration="1h",
                    request_max_limit=60,
                    request_reset_duration="1m",
                ),
            )
            if budget is not None:
                payload["budgets"] = [dict(max_limit=budget, reset_duration="1d")]
            created = client.post("/api/governance/virtual-keys", json=payload)
            created.raise_for_status()
            value = created.json()["virtual_key"]["value"]
            print(f"{variable}={value}")
    finally:
        if owned:
            client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.prepare:
            prepare_env(root)
            return
        load_dotenv(root / ".env")
        headers = {}
        if os.getenv("BIFROST_MANAGEMENT_TOKEN"):
            headers["Authorization"] = "Bearer " + os.environ["BIFROST_MANAGEMENT_TOKEN"]
        elif os.getenv("BIFROST_SETUP_TOKEN"):
            headers["X-Bifrost-Setup-Token"] = os.environ["BIFROST_SETUP_TOKEN"]
        else:
            raise ValueError("Set BIFROST_SETUP_TOKEN or BIFROST_MANAGEMENT_TOKEN in .env")
        bootstrap(os.getenv("BIFROST_BASE_URL", "http://localhost:8080"), headers)
    except (ValueError, KeyError, httpx.HTTPError) as exc:
        # HTTP exception text excludes response bodies; credentials are not printed.
        raise SystemExit(
            f"Bootstrap failed ({type(exc).__name__}); check gateway URL, version and management authentication."
        ) from None


if __name__ == "__main__":
    main()
