# Development Tips

## Start the portal locally

Use a provisioned Azure Developer CLI environment. The application loads the selected `azd` environment through `dotenv-azd`; do not assume a local `.env` file exists.

```shell
azd auth login
azd env select
.venv/bin/python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Existing shell environment variables override values loaded from `azd`.

For a clean restart, stop every listener on the development port before starting Uvicorn again:

```shell
for server_pid in $(lsof -tiTCP:8000 -sTCP:LISTEN); do kill "$server_pid"; done
.venv/bin/python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000
```

Use the actual port in both commands when working on another port, such as `49153`. With `--reload`, Python edits restart the worker automatically. Refresh the browser after static HTML, CSS, or JavaScript edits. When changing a referenced static asset, increment its query-string version in `app/backend/static/index.html` to prevent stale browser assets.

Useful checks:

```shell
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/api/knowledge-bases
```

## Tests

Install development and browser dependencies once:

```shell
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
```

Run fast backend tests while developing:

```shell
.venv/bin/python -m pytest tests/test_*.py -q
```

Run deterministic portal E2E tests:

```shell
.venv/bin/python -m pytest tests/e2e.py -q
```

These tests start an isolated Uvicorn server and mock Azure-dependent browser APIs. They do not require provisioned Azure resources. During iteration, use `-k` to target a workflow:

```shell
.venv/bin/python -m pytest tests/e2e.py -q -k 'part3_portal_workflow or part4_portal_workflow'
```

Run the same browser suite against real services from the selected provisioned `azd` environment:

```shell
.venv/bin/python -m pytest tests/e2e.py --live-smoke -v
```

Run model-judged portal acceptance against a deployed revision:

```shell
.venv/bin/python -m pytest tests/live_smoke.py --smoke-base-url "https://<app-hostname>" -v
```

Run Copilot SDK acceptance only when explicitly needed because it consumes GitHub Copilot quota:

```shell
.venv/bin/python -m pytest tests/copilot_smoke.py --copilot-smoke --smoke-base-url "https://<app-hostname>" -v
```

The Copilot smoke suite requires `GITHUB_TOKEN` or an authenticated GitHub CLI and `AZURE_SEARCH_QUERY_KEY` from the selected `azd` environment. It runs with isolated Copilot state and should not be used as the default regression test.

## Test selection

- Start with the narrowest relevant unit test or a focused `tests/e2e.py -k` expression.
- Run all deterministic E2E tests before finishing portal changes.
- Use `--live-smoke` only to verify integration with provisioned Azure resources.
- Use `tests/live_smoke.py` after deployment to verify the deployed portal and retrieval quality.
- Use `tests/copilot_smoke.py` sparingly for end-to-end workshop instruction validation.
