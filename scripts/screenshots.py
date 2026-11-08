"""Browser QA for a local receipt. Screenshots from scripted data are labelled MOCK.

Install: pip install '.[browser]'; python -m playwright install chromium
Run: python scripts/screenshots.py .penny/demo/MOCK-receipt.html --mock
"""

import argparse
import json
from pathlib import Path


def capture(source: Path, destination: Path, mock: bool):
    from playwright.sync_api import sync_playwright

    destination.mkdir(parents=True, exist_ok=True)
    findings = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for scheme in ("light", "dark"):
            for width in (360, 390, 768, 1024, 1280, 1536):
                page = browser.new_page(
                    viewport={"width": width, "height": 960},
                    color_scheme=scheme,
                    reduced_motion="reduce",
                )
                requests = []
                page.on(
                    "request",
                    lambda request, captured=requests: (
                        captured.append(request.url)
                        if request.url.startswith(("http://", "https://"))
                        else None
                    ),
                )
                errors = []
                page.on("pageerror", lambda error, captured=errors: captured.append(str(error)))
                page.goto(source.resolve().as_uri())
                page.wait_for_function("document.fonts.status === 'loaded'")
                assert page.locator("main h1").count() == 1
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
                    f"Page scroll at {width}/{scheme}"
                )
                page.keyboard.press("Tab")
                assert page.evaluate("document.activeElement.classList.contains('skip')")
                page.keyboard.press("Tab")
                assert page.evaluate("document.activeElement.id === 'theme'")
                page.keyboard.press("Enter")
                assert page.evaluate("document.documentElement.dataset.theme") in {"light", "dark"}
                page.keyboard.press("Enter")
                assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
                assert not errors and not requests, (errors, requests)
                label = "MOCK" if mock else "REAL"
                path = destination / f"{label}-receipt-{width}-{scheme}.png"
                page.screenshot(path=str(path), full_page=True)
                if width == 1280 and scheme == "light":
                    page.screenshot(path=str(destination / f"{label}-receipt-overview.png"))
                findings.append(
                    dict(
                        width=width,
                        scheme=scheme,
                        overflow=False,
                        keyboard=True,
                        reduced_motion=True,
                        external_requests=0,
                        js_errors=errors,
                        screenshot=path.name,
                    )
                )
                page.close()
        page = browser.new_page(viewport={"width": 1280, "height": 960})
        page.goto(source.resolve().as_uri())
        page.evaluate("document.body.style.zoom = '2'")
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (
            "Overflow at 200% zoom"
        )
        findings.append(dict(width=1280, zoom="200% CSS layout zoom", overflow=False))
        page.close()
        browser.close()
    (destination / f"{'MOCK' if mock else 'REAL'}-browser-checks.json").write_text(
        json.dumps(findings, indent=2), encoding="utf-8"
    )
    print(f"Verified {len(findings)} layouts. Screenshots: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("docs/screenshots"))
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    text = args.source.read_text(encoding="utf-8")
    if "MOCK" in text and not args.mock:
        parser.error("Receipt contains MOCK data: pass --mock to label screenshots")
    capture(args.source, args.output, args.mock)
