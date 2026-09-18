# Instructor guide

See [README.scenario.md](README.scenario.md) for the workshop narrative, evidence boundaries, and corpus design.

## Workshop portal deployment

The workshop portal is a FastAPI application deployed to Azure Container Apps. During `azd up`, an idempotent post-provision hook uploads the project-document and company-engineering-practice PDFs from [documents](documents) to separate Blob containers, runs an Azure AI Search Content Understanding pipeline for each corpus, and creates three shared knowledge bases. `cocoarynth-kb-docs` and `cocoarynth-kb-engineering-practices` each use minimal reasoning over one Search index; `cocoarynth-kb-all` uses low reasoning across both indexes. The attendee UI provides read-only corpus and chunk exploration, REST retrieval diagnostics, and calls through each native MCP endpoint.

The ingestion resources use Azure AI Search API `2026-05-01-preview`; knowledge-base retrieval and native MCP URLs use `2026-08-01-preview`.

Prerequisites:

- Azure Developer CLI 1.33 or later and [uv](https://docs.astral.sh/uv/)
- An Azure subscription with quota for `gpt-5.4-mini`, `text-embedding-3-large`, Azure AI Search Standard, and Azure Container Apps

Deploy the workshop portal:

```shell
azd auth login
azd env new <environment-name> --location eastus2
azd up
```

The deployment uses a user-assigned managed identity for backend-to-Search access. Search uses its managed identity to read both Blob corpora, write extracted images, and invoke the model deployments. The app returns the native MCP endpoint URLs but never returns the shared Search query key. Distribute the Search query key privately using the event-approved mechanism. Attendees connect to GitHub MCP directly with their event-provided GitHub accounts.

Running `azd provision` again compares SHA-256 metadata, uploads changed PDFs, removes stale corpus blobs, clears stale chunks, and reruns both indexers. The hook waits for both corpora to finish indexing before reporting success.

## Event operations

The GitHub Universe session is scheduled for Wednesday, October 28, 2026, from 1:00-2:30 PM PDT for 30 attendees. Attendees use prepared Surface laptops and event-provided GitHub accounts; they do not need Azure access or a local Python environment.

Before the session:

- Test Copilot CLI, the Copilot app, and VS Code on the event laptop image with an event-style GitHub account.
- Confirm that the hosted read-only GitHub MCP tools and all three native knowledge-base MCP endpoints work from the event network.
- Verify both corpora, both indexes, and all three knowledge bases in the deployed portal.
- Exercise expected classroom concurrency against the portal, Search service, and model deployments.
- Confirm the private Search query-key distribution method and the portal access mechanism.
- Tell attendees when the hosted environment will expire.

The shared Search query key grants query access across the lab Search service; it is not an attendee-specific authorization boundary. Use only synthetic content, keep the key out of chat, repositories, logs, and screenshots, and rotate it after the advertised access window. Direct GitHub MCP uses each attendee's GitHub authorization and must remain read-only for the workshop.

After the access window, rotate the distributed Search query key and remove the dedicated workshop resources when they are no longer needed.

## Local development

Authenticate with `azd auth login` and select a provisioned `azd` environment, then run:

```shell
python -m venv .venv
.venv/bin/pip install -r app/backend/requirements.txt
.venv/bin/uvicorn app.backend.main:app --reload
```

Local startup uses `dotenv-azd` to load values from the selected `azd` environment. Existing shell variables take precedence. In Azure Container Apps, `RUNNING_IN_PRODUCTION=true` disables local environment loading and selects the app's managed identity.

The inventory, chunk, and retrieval actions call Azure AI Search. Placeholder endpoints let the page load but return a clear `503` until they are replaced with a provisioned Search endpoint.

See [AGENTS.md](AGENTS.md) for server restart commands and the recommended test-selection workflow.

## Tests

Run the tests with:

```shell
.venv/bin/python -m unittest discover -s tests -v
```

Run the browser tests with:

```shell
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest tests/e2e.py -v
```

The Playwright suite starts an isolated Uvicorn server and mocks Azure-dependent browser requests, so it does not require deployed Azure resources.

To run the same browser flows as smoke tests against the selected, provisioned `azd` environment:

```shell
.venv/bin/python -m pytest tests/e2e.py --live-smoke -v
```

Live smoke mode does not inject placeholder settings or intercept API requests. It exits with a failure when the selected `azd` environment does not contain provisioned outputs.

To smoke-test a deployed revision directly:

```shell
.venv/bin/python -m pytest tests/live_smoke.py --smoke-base-url "https://<app-hostname>" -v
```

The live smoke suite runs the Part 3 and Part 4 portal workflows against the deployed app, then uses the configured Azure OpenAI chat deployment to judge the retrieved answers against acceptance rubrics.

To verify the Part 3 and Part 4 Copilot instructions with the GitHub Copilot SDK:

```shell
.venv/bin/python -m pytest tests/copilot_smoke.py --copilot-smoke --smoke-base-url "https://<app-hostname>" -v
```

This opt-in suite consumes Copilot quota and requires `GITHUB_TOKEN` or an authenticated GitHub CLI, plus `AZURE_SEARCH_QUERY_KEY`. It runs the SDK in isolated `empty` mode with a temporary Copilot home, so it does not read global Copilot configuration or credentials from Keychain. It clones `pamelafox/cocoarynth-trace` into a temporary directory, allows read-only MCP calls, denies shell and GitHub writes, and permits Part 4 to create only `origin-passport-csv-prd.md` through a scoped SDK tool.
