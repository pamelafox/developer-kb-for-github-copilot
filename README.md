# Building a developer knowledge base for GitHub Copilot

You are an engineer working for **Cocoarynth**, a fictional single-origin chocolate manufacturer. Your team builds **Cocoarynth Trace**, an application that traces chocolate from cacao harvest through production and shipment.

You will begin with the project code, then connect GitHub Copilot to live GitHub artifacts through GitHub MCP. Your instructor may present additional material between each part.

## Lab parts

1. [Part 1: Meet the project](part1.md)
2. [Part 2: Connect Copilot to GitHub](part2.md)
3. [Part 3: Connect Copilot to the document knowledge base](part3.md)
4. [Part 4: Use the combined knowledge base](part4.md)

Open only the part your instructor asks you to complete.

You do not need to install dependencies or run the application.

## Before you begin

Confirm that:

- You are signed in to the event-provided GitHub account.
- Your account can open [pamelafox/cocoarynth-trace](https://github.com/pamelafox/cocoarynth-trace) on GitHub.
- At least one of these clients is available: GitHub Copilot in VS Code, GitHub Copilot CLI, or GitHub Copilot App.

The repository is read-only for this lab. Do not create, edit, close, or comment on GitHub artifacts.

When the instructor is ready, begin with [Part 1](part1.md).

## Instructor deployment

The workshop portal is a FastAPI application deployed to Azure Container Apps. During `azd up`, an idempotent post-provision hook uploads the PDFs from [documents](documents) to Blob Storage, runs an Azure AI Search Content Understanding indexer, and creates two shared knowledge bases: `cocoarynth-kb-docs` for indexed documents and `cocoarynth-kb-all` for indexed documents plus live GitHub tools. The attendee UI provides read-only corpus and chunk exploration, retrieval testing, and native MCP configuration.

Prerequisites:

- Azure Developer CLI 1.33 or later and [uv](https://docs.astral.sh/uv/)
- An Azure subscription with quota for `gpt-5.4-mini`, `text-embedding-3-large`, Azure AI Search Standard, and Azure Container Apps
- A read-only fine-grained GitHub PAT that can access the workshop repository's code, issues, pull requests, and discussions

Configure `GITHUB_LAB_PAT` in the selected azd environment using your approved secret-management workflow, then deploy:

```shell
azd auth login
azd env new <environment-name> --location eastus2
azd up
```

The deployment uses a user-assigned managed identity for backend-to-Search access. Search uses its managed identity to read the Blob corpus, write extracted images, and invoke the model deployments. The app returns a shared Search query key only when an attendee requests native MCP configuration; it never returns the GitHub PAT.

Running `azd provision` again compares SHA-256 metadata, uploads changed PDFs, removes stale corpus blobs, clears stale chunks, and reruns the indexer. The hook waits for indexing to finish before reporting success.

For local development, authenticate with `azd auth login` and select a provisioned `azd` environment, then run:

```shell
python -m venv .venv
.venv/bin/pip install -r app/backend/requirements.txt
.venv/bin/uvicorn app.backend.main:app --reload
```

Local startup uses `dotenv-azd` to load values from the selected `azd` environment. Existing shell variables take precedence. In Azure Container Apps, `RUNNING_IN_PRODUCTION=true` disables local environment loading and selects the app's managed identity.

The inventory, chunk, and retrieval actions call Azure AI Search. Placeholder endpoints let the page load but return a clear `503` until they are replaced with a provisioned Search endpoint.

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
.venv/bin/python -m pytest tests/e2e.py --smoke-base-url "https://<app-hostname>" -v
```
