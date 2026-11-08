# Hosted demo and receipt viewer

Penny's Python coding agent operates on a local Git repository. The hosted website
is a project page, recorded MOCK workflow explorer, and browser-local receipt JSON
viewer. It does not expose a shell, edit a repository, run a model, or publish gateway
credentials. The included model actions/usage are explicitly labelled MOCK; its
filesystem patch and tests were executed during the recorded development demo.

## Build and preview

```bash
python -m pip install -e .
python scripts/build_web.py --output .penny/website-dist
python -m http.server 4173 --bind 127.0.0.1 --directory .penny/website-dist
```

Open `http://127.0.0.1:4173`. Static source is in `web/`; the build copies the licensed
fonts and renders the full receipt from `web/demo.json`. The fixture is a sanitized
export of the executed mock demo, with machine-specific command paths removed.
There is no frontend package installation or compilation step.

The viewer imports a run.json through the browser File API. The imported record is
rendered locally and is not uploaded. Treat displayed imported data as supplied,
not independently verified by the viewer.

## Hosting identity

Verified deployed URL: https://penny-coding-agent.heartyopossum3.chatgpt.site

The native publishing operation returned `succeeded` for deployment
`appgdep_6af0a74d97f08191b56884e1a5609a2a`, saved version
`appgprj_6af0a60e637c819193ce13b53ad9bddc~appgver_2b8ba5af15508191a9101c7957a7a839`,
from pushed static source commit `0ec25650c2e2f5a5a06e9f0208c7f06ca2315762`.

- Site: `appgprj_6af0a60e637c819193ce13b53ad9bddc`
- Audience: owner-private, the default for this deployment.
- Source checkout: `.penny/hosted-demo/`, separate from the CLI Git repository.
- Source manifest: `.penny/hosted-demo/.openai/hosting.json`, static directory `dist`.
- The Sites source helper pushes the exact rendered static tree and packages it;
  the saved version is deployed through the native Sites publishing tools.

Reuse this Site ID for future updates. Source write credentials are short-lived,
passed through stdin in memory and are not stored in the repository. Runtime
gateway credentials are not part of this website.

## Browser validation

Chromium checks passed at widths 360, 390, 768, 1280 and 1536: no horizontal page
overflow or JavaScript errors, timeline-step selection works, local run.json import
works, and the complete MOCK receipt loads. The screenshot was visually inspected.
The existing Python suite remains passing.
