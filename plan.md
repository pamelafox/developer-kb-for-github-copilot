# Building a developer knowledge base for GitHub Copilot

## Session

- **Event:** GitHub Universe 2026
- **Date:** Wednesday, October 28, 2026
- **Time:** 1:00-2:30 PM PDT
- **Duration:** 90 minutes
- **Attendance:** 30 people
- **Client options:** GitHub Copilot CLI, GitHub Copilot app, or GitHub Copilot in VS Code
- **Delivery:** Prepared Surface laptops and event-provided GitHub accounts, plus an instructor-hosted web application for ingestion and retrieval. No attendee Python environment is required.
- **Azure access:** Instructor-hosted resources in a demo tenant. Attendees will not have Azure passes, subscriptions, or Azure lab identities.
- **Take-home deliverable:** Repository containing the exercises, web application and ingestion/retrieval code, client configuration guidance, and full infrastructure for deployment into an attendee's own Azure environment.

The session flow follows [the organizer-facing outline](universe-session-outline.docx); the technical requirements below describe how to deliver it.

## Agreed approach

Use a **File Knowledge Source** for direct document uploads. Do not build a GitHub wiki connector, custom synchronization job, Blob ingestion pipeline, or attendee-managed indexer.

Attendees use an instructor-hosted web interface to create their own file knowledge source, documents-only knowledge base, GitHub MCP knowledge source, and combined knowledge base. The interface also supports document uploads, chunk visualization, and search testing. Its backend performs the Azure operations; attendees do not run notebooks or scripts locally.

The instructor provisions the Azure resources and web application and generates one shared, read-only GitHub lab PAT beforehand. The backend supplies that PAT when configuring GitHub knowledge sources; it is not distributed to attendees.

Privately provide attendees with the shared Search admin key and their KB's native MCP connection configuration. Copilot connects directly to Foundry IQ, not through an instructor-hosted MCP gateway. No attendee `.env` or model configuration is required. The secure distribution mechanism is still to be selected.

GitHub supplies live code, issues, PRs, and discussions. Uploaded files supply planning, architecture, and policy context. GitHub artifacts are not ingested in the required exercises.

## Learning outcomes

By the end of the lab, attendees can:

1. Start a Copilot conversation about a local repository and recognize tool permission requests.
2. Use GitHub MCP tools to investigate live engineering artifacts.
3. Upload documents into a File Knowledge Source, explore chunks, and test retrieval through a web interface.
4. Connect a knowledge base to Copilot through its native MCP endpoint and inspect supporting evidence.
5. Compare client-side coordination of separate MCP integrations with retrieval through a combined knowledge base.
6. Combine uploaded documents and live GitHub tools behind one knowledge base.
7. Identify how to adapt the supplied implementation and infrastructure to their own team.

## Framing and scenario

The central takeaway is that coding agents need relevant context beyond code. Existing MCP servers provide access to sources such as GitHub; Foundry IQ makes other documents searchable through a knowledge base's native MCP endpoint.

Open with the new-teammate analogy:

> Imagine joining a team with access to the codebase, but none of the planning documents. Could you explain why a feature was built the way it was?

Briefly illustrate how an answer spans a PR, an issue, and an architecture document. The hands-on sequence then starts with local code, adds GitHub artifacts, and introduces the planning documents during the ingestion exercise.

Attendees explore a fictional team's repository and ask, "Why was this feature built this way?" An export feature for an enterprise pilot remains a possible corpus, rather than a required release-decision exercise.

| Live GitHub evidence | Uploaded organizational context |
| --- | --- |
| Code showing implemented behavior | Enterprise pilot requirements |
| Merged and open PRs | An architecture decision explaining design constraints |
| Issues describing remaining work | Release and security policy |
| Discussions documenting decisions or exceptions | Optional support runbook |

Use a small, coherent set of short, text-rich documents. Include deliberate connections between document requirements and GitHub artifacts, as well as at least one real gap that requires evidence from both.

An example question requiring both document and GitHub evidence:

> Can we enable the export feature for the enterprise pilot? Identify the remaining work and cite the requirements and implementation evidence.

The precise fictional company, repository, document titles, and seeded artifacts remain to be authored.

## Lab outline

| Time | Duration | Section | Outcome |
| --- | --- | --- | --- |
| 0-15 minutes | 15 minutes | Opening: Get set up and meet your coding agent | Sign in, open the local repository, and have a first Copilot conversation |
| 15-30 minutes | 15 minutes | Opening: Connect Copilot to GitHub | Configure GitHub MCP and investigate live engineering artifacts |
| 30-45 minutes | 15 minutes | Section 1: Build a document knowledge base | Upload documents through the web interface, explore chunks, and test retrieval |
| 45-60 minutes | 15 minutes | Section 2: Connect Copilot to the document knowledge base | Query documents and GitHub evidence through separate MCP integrations |
| 60-80 minutes | 20 minutes | Section 3: Combine documents and live GitHub tools | Compare separate integrations with retrieval through a combined KB |
| 80-90 minutes | 10 minutes | Closing: Take the pattern back to your team | Recap the approaches and point to take-home infrastructure and learning resources |

Total: 90 minutes. Hands-on work and troubleshooting are included in the section timings. Chunk exploration and retrieval testing are part of Section 1; there is no standalone retrieval-tuning exercise or required release-readiness brief.

### Opening: Get set up and meet your coding agent

1. Introduce the lab's goal and briefly frame the new-teammate analogy.
2. Sign in with the provided GitHub account and open the prepared local repository.
3. Launch one client: Copilot CLI, the Copilot app, or VS Code.
4. Start a new chat, recognize tool permission requests, and inspect the agent's response.
5. Try a simple prompt such as "Explain what this project does and identify its main component."

This establishes a working Copilot client and a shared repository before introducing MCP configuration or new infrastructure.

Adapt the three client paths from the existing MCP tutorial. After setup, all paths use the same scenario and prompts.

### Opening: Connect Copilot to GitHub

1. Explain how MCP gives a coding agent access to tools and information beyond the local repository.
2. Configure the hosted GitHub MCP server for the chosen Copilot client.
3. Enable the read-only repository, issue, PR, and discussion tools needed by the exercises.
4. Ask, "Why was this feature built this way?"
5. Investigate relevant issues, PRs, and discussions, inspecting tool calls and supporting links.

This expands Copilot's context from local code to live engineering artifacts. Attendees use an existing MCP server before building a custom knowledge base. The hands-on document-context gap is introduced in the next section, not during client setup.

### Section 1: Build a document knowledge base

Introduce a planning document containing requirements or rationale not captured in GitHub. The intended gap is missing organizational context, not a contrived failure of GitHub search.

1. Open the instructor-hosted web interface and select or receive an attendee-specific resource prefix.
2. Create a Foundry IQ File Knowledge Source using the backend's preconfigured extraction and embedding settings.
3. Upload the supplied planning, architecture, and policy files.
4. Create a documents-only KB referencing that file source.
5. Explore the resulting index chunks and test retrieval in the web interface, inspecting passages and source references.

Adapt Section A of the Build26 notebook for the web application's backend, not for attendee execution. Keep resource names and relationships visible so attendees understand what they are creating.

The service handles extraction, chunking, embedding, and indexing. Each file source creates an underlying index, but no indexer or schedule. Upload processing is synchronous; the web interface must show processing status and errors and allow for ingestion latency.

Start with minimal retrieval and extractive output. Copilot will synthesize answers from the returned evidence in the next exercise.

### Section 2: Connect Copilot to the document knowledge base

1. Use the supplied client configuration to add the documents-only KB's native MCP endpoint directly to the chosen client.
2. Authenticate to that endpoint with the supplied Search admin key.
3. Ask questions that require the uploaded documents.
4. Ask a question requiring both GitHub and document evidence:

> What does the pilot require for export retention, and does the current implementation satisfy that requirement?

Inspect source references and distinguish requirements from implementation facts. At this point, **Copilot coordinates the separate GitHub and document-KB integrations**.

The core deliverable is complete by minute 60: an uploaded document collection exposed to Copilot through MCP.

### Section 3: Combine documents and live GitHub tools

1. Use the web interface to create an attendee-specific MCP Server knowledge source pointing to GitHub's hosted read-only MCP endpoint.
2. The backend configures `storedHeaders` authentication using the instructor-managed lab PAT and an explicit read-only tool allowlist. Attendees do not enter or receive the PAT.
3. Create a second KB referencing the existing file source and new GitHub MCP source.
4. Configure the combined KB with retrieval reasoning effort `low`; MCP knowledge sources do not support `minimal` in the documented preview contract.
5. Add the combined KB's native MCP endpoint directly to the chosen Copilot client using the supplied Search key.
6. Disable the separate GitHub and documents-only KB integrations and start a fresh comparison session.
7. Repeat a question requiring both sources, inspect the retrieved evidence, and compare the response with the previous exercise.

No second document upload or second document index is required. The two KBs reuse the same file source.

The architectural contrast:

| Separate integrations | Combined KB |
| --- | --- |
| Copilot plans calls to GitHub MCP and the documents KB | Foundry IQ plans retrieval across files and GitHub tools |
| Client-specific orchestration | Reusable multi-source retrieval configuration behind one endpoint |

Do not promise that a combined KB always produces a better answer or always selects every source.

### Closing: Take the pattern back to your team

Return to the new-teammate analogy: understanding a project requires both its engineering artifacts and the context behind them.

Recap the two approaches: connecting Copilot to separate MCP servers and combining sources behind a Foundry IQ knowledge base. Point attendees to the exercise repository, full infrastructure for their own Azure environment, and additional resources on MCP and retrieval best practices. State when the event environment expires and allow final questions.

Keep detailed guidance on replacing the corpus and choosing scheduled ingestion in the take-home materials rather than adding another hands-on activity during closing.

### Optional take-home extensions

- Compare minimal retrieval with extractive output against low retrieval effort with answer synthesis. Distinguish content extraction mode from retrieval reasoning effort and inspect evidence, not just wording.
- Draft a cited release-readiness brief with satisfied requirements, blockers, next actions, and explicit uncertainties.
- Update an uploaded file and observe the changed evidence. Direct file uploads are an explicitly managed collection, not automatic synchronization with the original files.

These extensions are outside the required 90-minute session.

## Scope and delivery

The instructor still needs to author the synthetic GitHub repositories and document corpus, with sample questions and supporting evidence. The web application for uploading files, visualizing chunks, testing search, and creating KBs also remains to be built.

Use a few slides to explain MCP, GitHub MCP, and Foundry IQ, including the contrast between client-side tool coordination and retrieval behind a combined KB. Attendees operate the workflow themselves rather than only watching a demo.

## Lab technical requirements

### Organizer and instructor responsibilities

- Organizers prepare the Surface laptops and test GitHub accounts, organization memberships, client access, and applicable policies.
- The instructor supplies the synthetic corpus, exercises, hosted web application, all Azure infrastructure, and lab-only credentials. Organizers do not provision Azure resources or identities.
- Laptop requirements are a current browser, Git, Copilot CLI, and VS Code with Copilot support, plus the Copilot app if supported on the event image.
- No attendee Python, Jupyter, `uv`, Docker, Azure CLI, or Azure Developer CLI setup is required. Codespaces is not required for the local laptop path.
- Laptop policies must permit GitHub sign-in, local configuration edits, tool permissions, and authenticated HTTPS MCP connections.

### GitHub accounts and artifacts

- Event-provided GitHub accounts with Copilot access and sufficient usage allowance.
- Organization policies permitting the selected clients, MCP integrations, and required GitHub authorization flows.
- Pre-created repository/repositories, organization memberships, code, issues, PRs, and discussions.
- A dedicated lab GitHub identity with only the access needed for the fictional corpus.
- One instructor-generated, fine-grained PAT with the read permissions required by the chosen tools, including contents, issues, PRs, and discussions as applicable.
- Any organization approval for that PAT completed before the lab.
- An expiration/revocation plan for the PAT after the event.

Use a shared organization and read-only engineering corpus for the required exercises. Repositories can be visible to other attendees because all content is synthetic. Each attendee has a separate local working copy; individual organizations or forks are not required. If optional exercises edit GitHub artifacts, provide individual repositories or otherwise prevent shared-state collisions.

### Azure infrastructure

The instructor provisions:

- A dedicated lab Azure AI Search service in a region supporting the required agentic retrieval features.
- An embedding deployment and a supported chat model deployment.
- Search managed identity access to the model resource, using the documented Cognitive Services User role.
- Hosting for the lab web frontend and backend.
- Network access from attendee environments to the web application, GitHub/Copilot services, and Search; from the backend to Search; and from Search to model endpoints and GitHub MCP.
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

The take-home infrastructure must create the required resources, web application hosting, and permissions, not depend on the instructor's existing deployments.

### Web application requirements

- Provide document upload, File Knowledge Source and KB creation, chunk visualization, and search testing from the browser.
- Let attendees create a combined KB that reuses their file source and adds the configured GitHub MCP source.
- Assign or collect unique attendee resource prefixes and retain the mapping to sources, file IDs, indexes, and KBs.
- Keep Azure resource-management operations and GitHub PAT handling in the backend, not in browser code.
- Provide native KB MCP endpoint configuration for each supported Copilot client; do not proxy Copilot's MCP requests through the web application.
- Show resource relationships, processing status, retrieved passages, source references, and actionable errors.
- Set upload and resource-creation limits suitable for a 30-person classroom and provide a recovery path if ingestion is slow or fails.
- Choose an event-appropriate access mechanism for the portal before deployment. It does not remove the shared Search key's service-wide permissions.

### Backend configuration and attendee connection details

The following variables are for instructor-managed backend configuration and take-home deployment, not an attendee-distributed `.env`:

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

Collect or assign the attendee prefix through the web interface. It must not be identical for all attendees.

Attendees receive only the lab web application URL, relevant repository URLs, their native KB MCP endpoint configuration, and the shared Search admin key. The GitHub lab PAT and model configuration stay in the backend configuration; the backend stores the PAT in each GitHub knowledge source as required.

Commit only `.env.example` with placeholders for backend/take-home setup. Ignore `.env` and credential-bearing client configuration. Select an event-approved private mechanism for distributing the Search key and connection details; do not publish secrets in the repository, application logs, screenshots, or a public download URL.

### Authentication paths

| Connection | Authentication |
| --- | --- |
| Attendee's Copilot client to GitHub MCP directly | Attendee's provided GitHub account, using the chosen client's supported flow |
| Attendee browser to lab web application | Event-appropriate portal access mechanism, to be selected; no Azure sign-in |
| Lab web application's backend to Azure AI Search | Instructor-configured Search admin key |
| Copilot client directly to a native KB MCP endpoint | Privately supplied shared Search admin key |
| Combined KB to GitHub MCP | Shared lab PAT stored by the backend in the attendee's MCP knowledge source |
| Azure AI Search to embedding/chat deployments | Preconfigured Search managed identity |

For downstream GitHub access, use `storedHeaders` with an `Authorization: Bearer <token>` header. Use `https://api.githubcopilot.com/mcp/readonly` and explicitly select the required toolsets and tools.

Attendees initiate creation of their GitHub knowledge sources through the web interface. The backend supplies credentials; a pre-created source is only a fallback, not the required path.

Do not use `foundryConnection`: this architecture calls the KB directly from Copilot, not through Foundry Agent Service. Per-user credential forwarding and OAuth token refresh are outside the required scope.

### Shared-service security boundary

This is a shared administrative lab environment, not a multi-tenant security design.

- The Search admin key grants service-wide data-plane access.
- Attendee prefixes prevent accidental naming collisions; they do not isolate access.
- Stored header masking does not provide isolation from other Search administrators.
- Keeping the GitHub PAT in the backend avoids distributing it as attendee configuration, but the web interface does not turn the shared Search service into an isolated multi-tenant environment.
- All combined KBs access GitHub as the shared lab identity, not as the individual attendee.
- Use only synthetic/non-sensitive lab content and a dedicated read-only lab PAT.
- Never use the instructor's normal personal PAT.
- Rotate the distributed Search key and revoke the PAT after the advertised lab access window.

### Implementation and client support

- Adapt the Build26 Section A file-upload and KB-creation code into the hosted backend.
- Include the frontend, backend, configuration examples, and deployment instructions in the take-home repository.
- Prepare the local repository and client setup on the Surface image; browser-based ingestion must not require attendee SDK installation.
- Support CLI, app, and VS Code setup, including authenticated HTTP MCP headers.
- Use clear, distinguishable names for the documents-only and combined KB MCP connections.
- Document how to disable competing integrations and start a fresh comparison session in each client.
- Keep secrets out of logs, public examples, and projected client configuration screens.
- Keep the planning corpus out of the baseline client's accessible project context until the upload exercise, where practical. Require evidence of KB tool use rather than mistaking local file reads for retrieval.

### API versions and ingestion behavior

- Target `2026-08-01-preview` for the combined file/MCP-source exercises and pin a compatible Python SDK in the backend.
- Apply the API version explicitly where supported; do not assume an environment variable changes SDK defaults.
- Pin and rehearse the supported client versions/configuration syntax before the event.
- Use minimal content extraction and a small set of text-rich files to keep processing predictable.
- Persist uploaded file IDs in the backend so repeated UI actions can update or delete existing files instead of duplicating them.
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

- Exercise the end-to-end flow on the actual Surface image with event-style GitHub accounts, not instructor credentials.
- Confirm all three clients can authenticate to the native KB MCP endpoint.
- Confirm the GitHub MCP source can authenticate and invoke the selected tools through Search.
- Exercise expected classroom concurrency against the web application, Search, model deployments, and the shared PAT's GitHub API rate limits.
- Prepare a populated documents KB and combined KB as recovery paths, while keeping attendee creation as the normal path.
- Provide observable progress during synchronous ingestion and clear recovery instructions. Rehearse the 15-minute ingestion block with the prepared corpus.
- Provide targeted cleanup by attendee prefix; do not use broad deletion against the shared service.
- State the event environment's expiration and provide independent deployment instructions in the take-home repository.

## Open preparation decisions

1. Secure delivery method for the shared Search key and native MCP connection configuration.
2. Fictional project, document corpus, and seeded GitHub evidence.
3. Shared repository versus individual repositories for any optional editing exercises.
4. Search tier, region, model deployments, and classroom capacity.
5. Exact SDK/client versions and final GitHub tool allowlist.
6. File citation-link handling and expected answer guide.
7. Duration of access to the instructor-hosted environment after the workshop.
8. Web application hosting, attendee access mechanism, and resource mapping.
9. Organizer approval for catalog abstract edits to reflect the revised client choices and delivery.

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
