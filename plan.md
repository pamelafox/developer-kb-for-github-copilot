# Building a developer knowledge base for GitHub Copilot

## Session

- **Event:** GitHub Universe 2026
- **Date:** Wednesday, October 28, 2026
- **Time:** 1:00-2:30 PM PDT
- **Duration:** 90 minutes
- **Attendance:** 30 people
- **Client options:** GitHub Copilot CLI, GitHub Copilot app, or GitHub Copilot in VS Code
- **Azure access:** Instructor-hosted resources in a demo tenant. Attendees will not have Azure passes, subscriptions, or Azure lab identities.
- **Take-home deliverable:** Repository containing the exercises, ingestion/retrieval code, client configuration guidance, and full infrastructure for deployment into an attendee's own Azure environment.

## Agreed approach

Use a **File Knowledge Source** for direct document uploads. Do not build a GitHub wiki connector, custom synchronization job, Blob ingestion pipeline, or attendee-managed indexer.

Attendees create their own file knowledge source, documents-only knowledge base, GitHub MCP knowledge source, and combined knowledge base. The instructor provisions the underlying Azure resources and generates one shared, read-only GitHub lab PAT beforehand.

Provide the Search endpoint, Search admin key, GitHub lab PAT, and non-secret model configuration through a shared `.env` file. The secure distribution mechanism is still to be selected.

GitHub supplies live code, issues, PRs, and discussions. Uploaded files supply planning, architecture, and policy context. GitHub artifacts are not ingested in the required exercises.

## Learning outcomes

By the end of the lab, attendees can:

1. Use GitHub MCP tools to investigate live engineering artifacts.
2. Upload documents into a File Knowledge Source and build a knowledge base.
3. Connect a knowledge base to Copilot through its native MCP endpoint.
4. Inspect retrieved evidence, citations, and retrieval activity.
5. Compare minimal retrieval with LLM-assisted retrieval.
6. Combine uploaded documents and live GitHub tools behind one knowledge base.
7. Produce a grounded developer work artifact and adapt the repository to their own environment.

## Scenario: Is this feature ready to ship?

Attendees join a fictional software team preparing an enterprise pilot. Their task is to determine whether an export feature is ready.

| Live GitHub evidence | Uploaded organizational context |
| --- | --- |
| Code showing implemented behavior | Enterprise pilot requirements |
| Merged and open PRs | An architecture decision explaining design constraints |
| Issues describing remaining work | Release and security policy |
| Discussions documenting decisions or exceptions | Optional support runbook |

Use a small, coherent set of short, text-rich documents. Include deliberate connections between document requirements and GitHub artifacts, as well as at least one real gap that requires evidence from both.

The central question:

> Can we enable the export feature for the enterprise pilot? Identify the remaining work and cite the requirements and implementation evidence.

The precise fictional company, repository, document titles, and seeded artifacts remain to be authored.

## Lab outline

| Time | Exercise | Outcome |
| --- | --- | --- |
| 0-15 minutes | 1. Connect Copilot to GitHub | Retrieve live engineering evidence and recognize missing planning context |
| 15-35 minutes | 2. Build a document knowledge base | Create a file source, upload documents, and query a documents-only KB |
| 35-50 minutes | 3. Connect the KB to Copilot | Combine document and GitHub evidence through separate MCP integrations |
| 50-60 minutes | 4. Inspect and tune retrieval | Understand evidence, activity, and retrieval reasoning choices |
| 60-80 minutes | 5. Build a combined knowledge base | Create a GitHub MCP source and combine it with the existing file source |
| 80-90 minutes | 6. Produce a release-readiness brief | Apply the setup to a useful developer workflow and explain adaptation |

### Exercise 1: Connect Copilot to GitHub

1. Sign in with the provided GitHub account and open the prepared lab repository/environment.
2. Choose one client: CLI, app, or VS Code.
3. Use the built-in GitHub MCP integration where available; otherwise configure the hosted server.
4. Enable the read-only repository, issue, PR, and discussion tools needed by the exercises.
5. Investigate what the export feature implements, relevant merged PRs, and remaining issues.
6. Ask whether the feature meets the enterprise pilot requirements.

The intended information gap is missing organizational context, not a contrived failure of GitHub search. The assistant should identify uncertainty rather than invent requirements.

Adapt the three client paths from the existing MCP tutorial. After setup, all paths use the same scenario and prompts.

### Exercise 2: Build a document knowledge base

Adapt Section A of the Build26 lab notebook.

1. Load the shared `.env` and set an attendee-specific resource prefix.
2. Create a File Knowledge Source using minimal content extraction and the preconfigured embedding deployment.
3. Upload the supplied planning, architecture, and policy files.
4. Create a documents-only KB referencing that file source.
5. Query the KB directly and inspect the retrieved passages and references.

The service handles extraction, chunking, embedding, and indexing. Each file source creates an underlying index, but no indexer or schedule. Upload processing is synchronous; show progress and allow for ingestion latency.

Start with minimal retrieval and extractive output. Copilot will synthesize answers from the returned evidence in the next exercise.

### Exercise 3: Give Copilot access to the knowledge base

1. Add the documents-only KB's native MCP endpoint to the chosen client.
2. Authenticate to that endpoint with the supplied Search admin key.
3. Ask questions that require the uploaded documents.
4. Ask a question requiring both GitHub and document evidence:

> What does the pilot require for export retention, and does the current implementation satisfy that requirement?

Inspect source references and distinguish requirements from implementation facts. At this point, **Copilot coordinates the separate GitHub and document-KB integrations**.

The core deliverable is complete by minute 50: an uploaded document collection exposed to Copilot through MCP.

### Exercise 4: Inspect and tune retrieval

Use the notebook or equivalent script to ask the same document question with two configurations:

| Configuration | Behavior to inspect |
| --- | --- |
| Minimal retrieval with extractive output | Direct retrieval of passages, without KB-side LLM query planning or answer synthesis |
| Low retrieval effort with answer synthesis | KB-side query planning and a synthesized response grounded in retrieved evidence |

Compare the retrieved evidence, references, activity, and completeness of the answer. Do not equate more polished wording with better grounding.

Explicitly distinguish **content extraction mode** from **retrieval reasoning effort**. Minimal file extraction can be used with low retrieval reasoning effort.

### Exercise 5: Combine documents and GitHub inside one KB

1. Load the instructor-provided GitHub lab PAT from `.env`.
2. Create an attendee-specific MCP Server knowledge source pointing to GitHub's hosted read-only MCP endpoint.
3. Configure `storedHeaders` authentication and an explicit read-only tool allowlist.
4. Create a second KB referencing the attendee's existing file source and new GitHub MCP source.
5. Set retrieval reasoning effort to `low`; MCP knowledge sources do not support `minimal` in the documented preview contract.
6. Add the combined KB's MCP endpoint to the chosen Copilot client.
7. Start a fresh session with the separate GitHub and documents-only KB integrations disabled for this comparison.
8. Ask the release-readiness question and inspect the evidence from both sources.

No second document upload or second document index is required. The two KBs reuse the same file source.

The architectural contrast:

| Separate integrations | Combined KB |
| --- | --- |
| Copilot plans calls to GitHub MCP and the documents KB | Foundry IQ plans retrieval across files and GitHub tools |
| Client-specific orchestration | Reusable multi-source retrieval configuration behind one endpoint |

Do not promise that a combined KB always produces a better answer or always selects every source.

### Exercise 6: Produce a useful work artifact

Use the combined KB to draft a release-readiness brief containing:

- Requirements already satisfied.
- Remaining blockers and proposed next actions.
- Links to supporting documents, issues, and PRs.
- Explicit uncertainties where evidence is missing.

Explain how to replace the fictional corpus, deploy the supplied infrastructure, and choose between direct uploads and scheduled ingestion in a real deployment.

Optional extension, outside the required 90-minute path: update an uploaded file and observe the changed evidence. Direct file uploads are an explicitly managed collection, not automatic synchronization with the original files.

## Lab technical requirements

### GitHub accounts and artifacts

- Event-provided GitHub accounts with Copilot access and sufficient usage allowance.
- Organization policies permitting the selected clients, MCP integrations, and required GitHub authorization flows.
- Pre-created repository/repositories, organization memberships, code, issues, PRs, and discussions.
- A dedicated lab GitHub identity with only the access needed for the fictional corpus.
- One instructor-generated, fine-grained PAT with the read permissions required by the chosen tools, including contents, issues, PRs, and discussions as applicable.
- Any organization approval for that PAT completed before the lab.
- An expiration/revocation plan for the PAT after the event.

Prefer a shared, read-only engineering corpus for the required exercises. If attendees edit GitHub artifacts, provide individual repositories or otherwise prevent shared-state collisions.

### Azure infrastructure

The instructor provisions:

- A dedicated lab Azure AI Search service in a region supporting the required agentic retrieval features.
- An embedding deployment and a supported chat model deployment.
- Search managed identity access to the model resource, using the documented Cognitive Services User role.
- Network access from attendee environments to Search and from Search to model endpoints and GitHub MCP.
- Applicable semantic ranking and agentic retrieval billing configuration.
- Capacity and service-tier limits sufficient for the classroom resource count and ingestion/query bursts.

Expected resources for 30 attendees, excluding fallback resources:

| Object | Per attendee | Classroom total |
| --- | --- | --- |
| File knowledge source | 1 | 30 |
| Generated document index | 1 | 30 |
| GitHub MCP knowledge source | 1 | 30 |
| Knowledge bases | 2 | 60 |

Budget for at least 60 knowledge sources total and headroom for instructor/fallback objects. Confirm the chosen tier's actual limits before selecting the service configuration.

No attendee Azure sign-in, Azure subscription, Blob credentials, or Storage provisioning is required. Prefer Search managed identity for model access so attendees do not also need an Azure OpenAI key.

The take-home infrastructure must create the required resources and permissions, not depend on the instructor's existing deployments.

### Shared environment configuration

Proposed `.env` variables:

| Variable | Purpose | Secret |
| --- | --- | --- |
| `AZURE_SEARCH_SERVICE_ENDPOINT` | Shared lab Search endpoint | No |
| `AZURE_SEARCH_ADMIN_KEY` | Create sources/KBs, upload files, and authenticate KB MCP requests | Yes |
| `GITHUB_LAB_PAT` | Authenticate Search's downstream GitHub MCP calls | Yes |
| `GITHUB_LAB_OWNER` | GitHub organization or repository owner | No |
| `GITHUB_LAB_REPO` | Target repository for the scenario | No |
| `AZURE_OPENAI_ENDPOINT` | Model endpoint used by Search | No |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name | No |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model name | No |
| `AZURE_OPENAI_CHATGPT_DEPLOYMENT` | Retrieval planning/synthesis deployment name | No |
| `AZURE_OPENAI_CHATGPT_MODEL_NAME` | Chat model name | No |
| `AZURE_SEARCH_API_VERSION` | API version used consistently across SDK clients and MCP URLs | No |

Collect the attendee prefix separately, or add it locally after downloading the shared configuration. It must not be identical for all attendees.

Commit only `.env.example` with placeholders. Ignore `.env` and any local credential-bearing client configuration. Select an event-approved private distribution mechanism; do not publish secrets in the repository, notebook outputs, screenshots, or a public download URL.

### Authentication paths

| Connection | Authentication |
| --- | --- |
| Attendee's Copilot client to GitHub MCP directly | Attendee's provided GitHub account, using the chosen client's supported flow |
| Attendee notebook/script to Azure AI Search | Shared Search admin key |
| Copilot client to a KB MCP endpoint | Shared Search admin key |
| Combined KB to GitHub MCP | Shared lab PAT stored by the attendee in their MCP knowledge source |
| Azure AI Search to embedding/chat deployments | Preconfigured Search managed identity |

For downstream GitHub access, use `storedHeaders` with an `Authorization: Bearer <token>` header. Use `https://api.githubcopilot.com/mcp/readonly` and explicitly select the required toolsets and tools.

Attendees create their own GitHub knowledge sources in the exercise. The instructor supplies the PAT, not a pre-created source for the required path.

Do not use `foundryConnection`: this architecture calls the KB directly from Copilot, not through Foundry Agent Service. Per-user credential forwarding and OAuth token refresh are outside the required scope.

### Shared-service security boundary

This is a shared administrative lab environment, not a multi-tenant security design.

- The Search admin key grants service-wide data-plane access.
- Attendee prefixes prevent accidental naming collisions; they do not isolate access.
- Stored header masking does not provide isolation from other Search administrators.
- All combined KBs access GitHub as the shared lab identity, not as the individual attendee.
- Use only synthetic/non-sensitive lab content and a dedicated read-only lab PAT.
- Never use the instructor's normal personal PAT.
- Rotate the distributed Search key and revoke the PAT after the advertised lab access window.

### Exercise code and client support

- Provide a notebook adapted from Build26 Section A plus runnable scripts for terminal-oriented attendees.
- Share implementation helpers between notebook and scripts to avoid maintaining divergent versions.
- Supply Codespaces/dev-container configuration and a local setup path.
- Support CLI, app, and VS Code setup, including authenticated HTTP MCP headers.
- Use clear, distinguishable names for the documents-only and combined KB MCP connections.
- Document how to disable competing integrations and start a fresh comparison session in each client.
- Keep secrets out of printed setup commands and saved notebook outputs.
- Keep the planning corpus out of the baseline client's accessible project context until the upload exercise, where practical. Require evidence of KB tool use rather than mistaking local file reads for retrieval.

### API versions and ingestion behavior

- Target `2026-08-01-preview` for the combined file/MCP-source exercises and pin a compatible Python SDK.
- Apply the API version explicitly where supported; do not assume an environment variable changes SDK defaults.
- Pin and rehearse the supported client versions/configuration syntax before the event.
- Use minimal content extraction and a small set of text-rich files to keep processing predictable.
- Persist uploaded file IDs so reruns can update or delete existing files instead of duplicating them.
- Do not assume uploading the same filename replaces its previous content.
- Surface upload and retrieval failures clearly. Account for the documented upload processing duration of up to 180 seconds.
- Keep automatic retries aware of non-idempotent upload behavior.
- Do not introduce scheduled ingestion or source synchronization into the required exercises.

### Grounding and citations

- Include stable original document URLs or an explicit mapping from uploaded file IDs/names to source links.
- Establish how those links appear in actual file-source retrieval references and MCP answers; do not assume arbitrary upload metadata automatically becomes a citation.
- Preserve source identifiers needed to attribute GitHub tool results.
- Inspect tool-output parsing and truncation so relevant GitHub evidence survives retrieval.
- Include an answer guide mapping each expected conclusion to its supporting artifacts.
- Accept explicit uncertainty where the corpus lacks evidence.

### Classroom reliability and cleanup

- Exercise the end-to-end flow with event-style GitHub accounts, not instructor credentials.
- Confirm all three clients can authenticate to the native KB MCP endpoint.
- Confirm the GitHub MCP source can authenticate and invoke the selected tools through Search.
- Exercise expected classroom concurrency against Search, model deployments, and the shared PAT's GitHub API rate limits.
- Prepare a populated documents KB and combined KB as recovery paths, while keeping attendee creation as the normal path.
- Provide observable progress during synchronous ingestion and clear recovery instructions.
- Provide targeted cleanup by attendee prefix; do not use broad deletion against the shared service.
- State the event environment's expiration and provide independent deployment instructions in the take-home repository.

## Open preparation decisions

1. Secure delivery method for the shared `.env`.
2. Fictional project, document corpus, and seeded GitHub evidence.
3. Shared repository versus individual repositories for any optional editing exercises.
4. Search tier, region, model deployments, and classroom capacity.
5. Exact SDK/client versions and final GitHub tool allowlist.
6. File citation-link handling and expected answer guide.
7. Duration of access to the instructor-hosted environment after the workshop.

## References

- [Universe session listing](https://reg.githubuniverse.com/flow/github/universe26/attendee-portal/page/sessioncatalog/session/1777700808239001XZyK)
- [Existing three-client MCP setup exercise](https://github.com/pamelafox/github-copilot-mcp-tutorial/blob/main/exercise1.md)
- [Build26 File Knowledge Source notebook](https://github.com/microsoft/Build26-LAB532-from-data-to-context-agent-ready-knowledge-with-foundry-iq/blob/main/notebooks/part1-standard-foundry-iq-kb.ipynb)
- [File Knowledge Source documentation](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-file?pivots=python)
- [MCP Server knowledge source documentation](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-mcp-server?pivots=python)
- [Knowledge-base retrieval and native MCP endpoint](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-retrieve#call-the-mcp-endpoint)
- [Retrieval reasoning effort](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [GitHub hosted MCP configuration](https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md)
- [GitHub MCP authentication and governance](https://github.com/github/github-mcp-server/blob/main/docs/policies-and-governance.md)
