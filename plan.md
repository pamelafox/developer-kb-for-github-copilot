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

Use two instructor-managed **Search Index Knowledge Sources** over explicit Azure AI Search indexes. Pre-ingest the project-document and company-engineering-practice corpora from separate standard Blob Storage containers during deployment with Content Understanding skillsets; do not use ADLS Gen2 ACL ingestion, a GitHub wiki connector, or attendee-managed indexers.

Attendees use an instructor-hosted web interface to explore the project-document corpus and chunks, test retrieval, and connect two pre-created shared knowledge bases. `cocoarynth-kb-docs` contains project documents; `cocoarynth-kb-all` combines project documents with company engineering and design guidance from a second index. Attendees do not create Azure resources, upload documents, or run notebooks or scripts locally.

Privately provide attendees with the shared Search query key and their KB's native MCP connection configuration. Copilot connects directly to Foundry IQ, not through an instructor-hosted MCP gateway. No attendee `.env` or model configuration is required. The secure distribution mechanism is still to be selected.

Direct GitHub MCP supplies live code, issues, PRs, and discussions using each attendee's GitHub authorization. The two Blob-backed Search indexes supply project requirements and company standards. GitHub artifacts are not ingested in the required exercises.

## Learning outcomes

By the end of the lab, attendees can:

1. Start a Copilot conversation about a local repository and recognize tool permission requests.
2. Use GitHub MCP tools to investigate live engineering artifacts.
3. Explore pre-ingested documents and chunks and test retrieval through a web interface.
4. Connect a knowledge base to Copilot through its native MCP endpoint and inspect supporting evidence.
5. Explain the boundary between Foundry IQ planning across two indexes and Copilot coordinating the KB with direct GitHub MCP.
6. Create a locally saved, source-grounded PRD from project documents, company standards, and live GitHub evidence.
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
| 30-45 minutes | 15 minutes | Section 1: Explore a document knowledge base | Explore the pre-ingested corpus and chunks, then test retrieval |
| 45-60 minutes | 15 minutes | Section 2: Connect Copilot to the document knowledge base | Query documents and GitHub evidence through separate MCP integrations |
| 60-80 minutes | 20 minutes | Section 3: Create a grounded PRD | Combine project documents, company standards, and live GitHub evidence |
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

### Section 1: Explore a document knowledge base

Introduce a planning document containing requirements or rationale not captured in GitHub. The intended gap is missing organizational context, not a contrived failure of GitHub search.

1. Open the instructor-hosted web interface and inspect the pre-ingested corpus inventory.
2. Review the shared Search Index Knowledge Source and documents-only KB relationship.
3. Explore the Content Understanding output and indexed chunks.
4. Test retrieval in the web interface, inspecting passages and source references.

Adapt the LTG242 Content Understanding indexer pattern for the deployment hook, not for attendee execution. Keep resource names and relationships visible so attendees understand how the corpus was prepared.

The Content Understanding skill extracts text, images, and location metadata, performs semantic chunking, and feeds an embedding skill before attendees arrive. The shared Blob indexer runs on demand during deployment, with no recurring schedule. The instructor verifies indexer status and retrieval during deployment rehearsal.

Start with minimal retrieval and extractive output. Copilot will synthesize answers from the returned evidence in the next exercise.

### Section 2: Connect Copilot to the document knowledge base

1. Use the supplied client configuration to add the documents-only KB's native MCP endpoint directly to the chosen client.
2. Authenticate to that endpoint with the supplied Search query key.
3. Ask questions that require the uploaded documents.
4. Ask a question requiring both GitHub and document evidence:

> What does the pilot require for export retention, and does the current implementation satisfy that requirement?

Inspect source references and distinguish requirements from implementation facts. At this point, **Copilot coordinates the separate GitHub and document-KB integrations**.

The core deliverable is complete by minute 60: a pre-ingested document collection explored in the browser and exposed to Copilot through MCP.

### Section 3: Create a grounded PRD

1. Review the two Search Index knowledge sources: project documents and Cocoarynth engineering practices.
2. Use the pre-created `cocoarynth-kb-all`, which references both Search Index knowledge sources.
3. Configure the combined KB with retrieval reasoning effort `medium` so it can use iterative retrieval across both indexes.
4. Add the combined KB's native MCP endpoint directly to the chosen Copilot client using the supplied Search query key.
5. Disable only the documents-only KB. Keep direct GitHub MCP enabled and start a fresh session.
6. Ask Copilot to create a local Markdown PRD for CSV Origin Passport support using direct GitHub evidence plus requirements and standards from the combined KB.
7. Inspect tool activity and verify that the PRD distinguishes requirements, current implementation, and recommendations with source links.

No attendee document upload or additional index is required. Both indexes are prepared before the session.

The architectural contrast:

| Layer | Responsibility |
| --- | --- |
| Foundry IQ | Plans retrieval across project-document and engineering-practice indexes behind one endpoint |
| GitHub Copilot | Coordinates the combined KB, direct GitHub MCP, and local workspace |
| Direct GitHub MCP | Retrieves live repository evidence with attendee authorization |

Do not promise that a combined KB always produces a better answer or always selects every source.

### Closing: Take the pattern back to your team

Return to the new-teammate analogy: understanding a project requires both its engineering artifacts and the context behind them.

Recap the two coordination layers: Foundry IQ planning across indexed organizational knowledge and Copilot coordinating that KB with direct GitHub tools. Point attendees to the exercise repository, full infrastructure for their own Azure environment, and additional resources on MCP and retrieval best practices. State when the event environment expires and allow final questions.

Keep detailed guidance on replacing the corpus and choosing scheduled ingestion in the take-home materials rather than adding another hands-on activity during closing.

### Optional take-home extensions

- Compare the document-only and combined retrieval configurations with extractive output. Distinguish output mode from retrieval reasoning effort and inspect evidence, not just wording.
- Draft a cited release-readiness brief with satisfied requirements, blockers, next actions, and explicit uncertainties.
- Update a corpus PDF, rerun the deployment hook, and observe the changed indexed evidence.

These extensions are outside the required 90-minute session.

## Scope and delivery

The instructor maintains the synthetic GitHub repository and document corpus, with sample questions and supporting evidence. Deployment pre-ingests the corpora and creates three shared KBs; the hosted application supports read-only exploration, retrieval testing, and connection configuration.

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

| Object | Shared | Per attendee | Classroom total |
| --- | --- | --- | --- |
| Search index knowledge source | 2 | 0 | 2 |
| Blob data source, skillset, and indexer | 2 each | 0 | 2 each |
| Search index | 2 | 0 | 2 |
| Knowledge bases | 3 | 0 | 3 |

Budget for two knowledge sources and three knowledge bases, plus headroom for fallback objects. Confirm the chosen tier's actual limits before selecting the service configuration.

No attendee Azure sign-in, Azure subscription, Blob credentials, or Storage provisioning is required. Search uses managed identity for Blob and model access so attendees do not need storage or Azure OpenAI keys.

The take-home infrastructure must create the required resources, web application hosting, and permissions, not depend on the instructor's existing deployments.

### Web application requirements

- Provide read-only corpus inventory, chunk visualization, and retrieval testing from the browser.
- Provide read-only access to both single-index KBs and the combined KB.
- Pre-create both Search Index knowledge sources and the combined KB during deployment.
- Keep Azure resource-management operations and GitHub PAT handling in the backend, not in browser code.
- Provide native KB MCP endpoint configuration for each supported Copilot client; do not proxy Copilot's MCP requests through the web application.
- Show resource relationships, processing status, retrieved passages, source references, and actionable errors.
- Pre-ingest and verify the shared corpus before the session and provide a populated fallback KB if ingestion fails.
- Choose an event-appropriate access mechanism for the portal before deployment. It does not remove the shared Search key's service-wide permissions.

### Backend configuration and attendee connection details

The following variables are for instructor-managed backend configuration and take-home deployment, not an attendee-distributed `.env`:

| Variable | Purpose | Secret |
| --- | --- | --- |
| `AZURE_SEARCH_ENDPOINT` | Shared lab Search endpoint | No |
| `AZURE_SEARCH_QUERY_KEY` | Authenticate attendee KB MCP retrieval requests | Yes |
| `AZURE_OPENAI_ENDPOINT` | Model endpoint used by Search | No |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embedding deployment name | No |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model name | No |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Retrieval planning/synthesis deployment name | No |
| `AZURE_OPENAI_CHAT_MODEL` | Chat model name | No |
| `AZURE_AI_FOUNDRY_ENDPOINT` | AI Services endpoint used by Content Understanding | No |
| `AZURE_STORAGE_ACCOUNT_NAME` | Blob account containing the instructor corpus | No |
| `AZURE_STORAGE_ACCOUNT_ID` | Resource ID used by the Search data source and knowledge store | No |
| `AZURE_CLIENT_ID` | User-assigned managed identity used by the Container App | No |

Attendees receive only the lab web application URL, relevant repository URLs, and their native KB MCP endpoint configuration containing the shared Search query key. Model configuration stays in the backend configuration. GitHub MCP authenticates directly through each attendee's event-provided GitHub account.

Use the selected `azd` environment for local backend configuration; `dotenv-azd` loads its values at startup. Ignore `.env` and credential-bearing client configuration. Select an event-approved private mechanism for distributing the Search key and connection details; do not publish secrets in the repository, application logs, screenshots, or a public download URL.

### Authentication paths

| Connection | Authentication |
| --- | --- |
| Attendee's Copilot client to GitHub MCP directly | Attendee's provided GitHub account, using the chosen client's supported flow |
| Attendee browser to lab web application | Event-appropriate portal access mechanism, to be selected; no Azure sign-in |
| Lab web application's backend to Azure AI Search | Container App user-assigned managed identity with Search Service Contributor and Search Index Data Contributor roles |
| Copilot client directly to a native KB MCP endpoint | Privately supplied shared Search query key |
| Azure AI Search to embedding/chat deployments | Preconfigured Search managed identity |
| Azure AI Search to Blob corpora and extracted images | Search managed identity with Storage Blob Data Contributor |

Use GitHub's hosted read-only MCP endpoint directly from the attendee's Copilot client and explicitly select the required read-only toolsets. Do not place GitHub credentials in the workshop backend or a Search knowledge source.

### Shared-service security boundary

This is a shared administrative lab environment, not a multi-tenant security design.

- The shared Search query key grants read-only query access across the lab Search service; it is not a per-attendee authorization boundary.
- The web interface does not turn the shared Search service into an isolated multi-tenant environment.
- Direct GitHub access uses the attendee's event-provided account and repository permissions.
- Use only synthetic, non-sensitive lab content and read-only GitHub toolsets.
- Rotate the distributed Search key after the advertised lab access window.

### Implementation and client support

- Adapt the LTG242 Blob, Content Understanding, indexer, and Search Index Knowledge Source pattern into two idempotent instructor-run pipelines in the post-provision step.
- Include the frontend, backend, configuration examples, and deployment instructions in the take-home repository.
- Prepare the local repository and client setup on the Surface image; browser-based ingestion must not require attendee SDK installation.
- Support CLI, app, and VS Code setup, including authenticated HTTP MCP headers.
- Use clear, distinguishable names for the documents-only and combined KB MCP connections.
- Document how to disable competing integrations and start a fresh comparison session in each client.
- Keep secrets out of logs, public examples, and projected client configuration screens.
- Keep the planning corpus out of the baseline client's accessible project context. Require evidence of KB tool use rather than mistaking local file reads for retrieval.

### API versions and ingestion behavior

- Target `2026-05-01-preview` for the Content Understanding indexer resources and `2026-08-01-preview` for native knowledge-base MCP endpoints; pin a compatible Python SDK in the backend.
- Apply the API version explicitly where supported; do not assume an environment variable changes SDK defaults.
- Pin and rehearse the supported client versions/configuration syntax before the event.
- Use Content Understanding semantic chunking and two small sets of text-rich files to keep processing predictable.
- The post-provision script compares Blob SHA-256 metadata independently for both corpora, uploads changed PDFs, removes stale files and chunks, and reruns both indexers.
- Surface retrieval failures clearly and verify the documented upload processing duration before attendees arrive.
- Do not introduce scheduled ingestion or source synchronization into the required exercises.

### Grounding and citations

- Include stable original document URLs or an explicit mapping from uploaded file IDs/names to source links.
- Establish how Blob paths and page metadata appear in Search Index Knowledge Source retrieval references and MCP answers.
- Preserve source identifiers needed to attribute GitHub tool results.
- Inspect tool-output parsing and truncation so relevant GitHub evidence survives retrieval.
- Include an answer guide mapping each expected conclusion to its supporting artifacts.
- Accept explicit uncertainty where the corpus lacks evidence.

### Classroom reliability and cleanup

- Exercise the end-to-end flow on the actual Surface image with event-style GitHub accounts, not instructor credentials.
- Confirm all three clients can authenticate to the native KB MCP endpoint.
- Confirm direct GitHub MCP can authenticate with event-style attendee accounts and invoke the selected read-only tools.
- Exercise expected classroom concurrency against the web application, Search, model deployments, and the shared PAT's GitHub API rate limits.
- Prepare a populated documents KB and combined KB as recovery paths, while keeping attendee creation as the normal path.
- Provide observable progress during synchronous ingestion and clear recovery instructions. Rehearse the 15-minute ingestion block with the prepared corpus.
- Clean up the dedicated shared lab resources after the event access window.
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
- [LTG242 Content Understanding index pipeline](https://github.com/microsoft/aitour27-LTG242-knowledge-retrieval-for-ai-agents-with-foundry-iq/blob/main/infra/create-search-indexes.py)
- [Search Index Knowledge Source documentation](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-search-index)
- [MCP Server knowledge source documentation](https://learn.microsoft.com/en-us/azure/search/agentic-knowledge-source-how-to-mcp-server?pivots=python)
- [Knowledge-base retrieval and native MCP endpoint](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-retrieve#call-the-mcp-endpoint)
- [Retrieval reasoning effort](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-set-retrieval-reasoning-effort)
- [GitHub hosted MCP configuration](https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md)
- [GitHub MCP authentication and governance](https://github.com/github/github-mcp-server/blob/main/docs/policies-and-governance.md)
