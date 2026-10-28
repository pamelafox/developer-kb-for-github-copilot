# Exercise 3: Connect Copilot to a document retrieval MCP server

In this exercise, you will explore Cocoarynth's pre-ingested document collection, test retrieval over MCP in the workshop portal, and connect GitHub Copilot to the document retrieval server.

## Contents

- [1. Explore the document corpus](#1-explore-the-document-corpus)
- [2. Connect GitHub Copilot](#2-connect-github-copilot)
- [3. Start a fresh chat](#3-start-a-fresh-chat)
- [4. Test document retrieval](#4-test-document-retrieval)
- [5. Combine document and GitHub evidence](#5-combine-document-and-github-evidence)
- [6. Check your understanding](#6-check-your-understanding)

## 1. Explore the document corpus

Your instructor has already indexed Cocoarynth documents into a Foundry IQ service using an Azure account. Since you do not have Azure accounts in this workshop, you will explore the Foundry IQ service using a special portal. If you're curious to see the code that ingested the documents, check out [foundry_iq.py](app/backend/foundry_iq.py).

### Inspect the documents

The Cocoarynth documents are stored in Azure Blob Storage. These documents contain organizational context that is not available from application code or the GitHub repository.

1. Open the provided portal URL.
2. Under **Corpus 1: Project requirements**, select **Browse documents**.
3. Review the pre-ingested document inventory.
4. Open each document and identify its purpose: pilot requirements, architecture decision, data-sharing policy, or support runbook.

### Inspect the chunks

As part of the Foundry IQ ingestion pipeline, Azure Content Understanding extracted the content and metadata, and chunked the documents based on semantic boundaries.

1. Under **Corpus 1: Project requirements**, select **View document chunks**.
2. Select the document named "mapayca-markets-traceability-pilot-requirements.pdf".
3. Review the chunks in page order.
4. Inspect the page metadata and notice where one semantic topic ends and another begins.
5. Select at least one other document and compare its chunk boundaries.

### Search the chunk index

The Foundry IQ search index contains all the document chunks, with vector embeddings for each one. You can directly query this search index using hybrid search, a combination of vector search and keyword search.

1. Under **Corpus 1: Project requirements**, select **Search the index**.
2. Search for `CSV export requirements`.
3. Inspect the matching passages, source documents, page numbers, and relevance scores.
4. Run a second search for `information excluded from wholesale exports`.

### Call document retrieval over MCP

MCP is a standard way for an AI application to discover and call tools. The workshop portal can call the `knowledge_base_retrieve` tool exposed for this corpus, so you can compare its content blocks with direct index search before connecting Copilot.

1. Under **Corpus 1: Project requirements**, select **Call over MCP**.
2. Ask: “What must change in the Origin Passport export for the Mapayça Markets pilot?”
3. Inspect the MCP content blocks returned by `knowledge_base_retrieve`. Confirm that the first block contains the evidence array and each remaining block contains one reference.
4. Match each evidence record to its reference using `ref_id`.
5. Compare the retrieved passages with the results from **Search the index**.

Before continuing, make sure you can explain the difference between a source document, an indexed chunk, direct hybrid search, and an MCP tool call.

## 2. Connect GitHub Copilot

Follow the instructions for the Copilot client you selected in Exercise 1.

The Foundry IQ MCP endpoint and API key are both listed at the provided secrets URL. The query key is a shared workshop credential that gives read-only access to the knowledge base. Do not paste the key into chat, commit it to the repository, include it in screenshots, or share it with anyone outside the workshop.

### Option A: Configure the MCP server in Copilot App

1. Open the GitHub Copilot App.
2. Select **Customize** in the sidebar.
3. Open the **Add** menu in the top-right corner, then select **MCP Server**.
4. Enter `cocoarynth-kb-docs` for the server name.
5. Select **HTTP**.
6. Paste the `cocoarynth-kb-docs` MCP endpoint into the URL field. Copy it from the provided secrets URL.
7. Under **Headers**, select **Add header**.
8. Enter `api-key` for the header name and paste the key from the provided secrets URL for its value.
9. Leave other fields at their defaults, then select **Add server**.
10. Confirm that `github` and `cocoarynth-kb-docs` are both listed in the **Installed** tab.

### Option B: Configure the MCP server in Copilot CLI

1. Exit the active interactive Copilot session if one is running.
2. In a terminal prompt, configure Copilot CLI with the Foundry IQ MCP server, replacing both placeholders with the `cocoarynth-kb-docs` MCP endpoint and Search query key:

   ```shell
   copilot mcp add --transport http --header "api-key: <SEARCH_QUERY_KEY>" cocoarynth-kb-docs "<DOCUMENTS_KB_MCP_ENDPOINT>"
   ```

   The full command, with both values filled in, is at the provided secrets URL so you can also paste it directly.

   If prompted to remove a previous `cocoarynth-kb-docs` MCP server, run the provided command.

3. From a terminal prompt, start a new Copilot CLI session:

   ```shell
   copilot
   ```

4. Inside the session, display the installed MCP servers with this slash command:

   ```text
   /mcp show
   ```

5. In the server listing, confirm that the `cocarynth-kb-all` server and `github` servers are both installed and enabled.

### Option C: Configure the MCP server in VS Code

1. Open `.vscode/mcp.json` in the local checkout.
2. Keep the existing `github` server and add the `cocoarynth-kb-docs` server and secure input shown below.
3. Replace `<DOCUMENTS_KB_MCP_ENDPOINT>` with the `cocoarynth-kb-docs` MCP endpoint from the portal or the provided secrets URL.

   ```json
   {
     "inputs": [
       {
         "id": "cocoarynth-search-key",
         "type": "promptString",
         "description": "Cocoarynth workshop Search query key",
         "password": true
       }
     ],
     "servers": {
       "github": {
         "type": "http",
         "url": "https://api.githubcopilot.com/mcp/readonly",
         "headers": {
           "X-MCP-Toolsets": "repos,issues,pull_requests,discussions"
         }
       },
       "cocoarynth-kb-docs": {
         "type": "http",
         "url": "<DOCUMENTS_KB_MCP_ENDPOINT>",
         "headers": {
           "api-key": "${input:cocoarynth-search-key}"
         }
       }
     }
   }
   ```

4. Save the file.
5. Select **Start** above `cocoarynth-kb-docs`, or run **MCP: List Servers** from the Command Palette and start it.
6. Enter the Search query key from the provided secrets URL when VS Code prompts for it.
7. Confirm that both `github` and `cocoarynth-kb-docs` are running.
8. In Copilot Chat, select the tools icon and confirm that tools from both servers are available.

## 3. Start a fresh chat

Start a new session so you can clearly observe which integrations Copilot uses. In the Copilot App, start the session from the Cocoarynth Trace project. In VS Code, make sure the chat is in Agent mode.

Both separate integrations should remain enabled:

- `github` supplies live code, issues, pull requests, and discussions.
- `cocoarynth-kb-docs` supplies the uploaded requirements, policy, architecture decision, and support runbook.

## 4. Test document retrieval

First ask a question that can be answered from the uploaded documents:

> What file format does Mapayça Markets require for the Cocoarynth traceability pilot, and does its importer accept JSON? Cite the supporting document.

Check that Copilot:

- Calls a tool from `cocoarynth-kb-docs`. Expand the tool call to see the arguments passed to the `knowledge_base_retrieve` tool.
- Responds that CSV is the required format, not JSON.
- Cites the Mapayça Markets pilot requirements PDF rather than local code or a GitHub issue.

## 5. Combine document and GitHub evidence

Now ask a question that requires both integrations:

> Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker, check relevant issues for related open work (using GitHub MCP), and cite both the pilot requirements and current implementation evidence.

Inspect the tool calls and answer. Copilot should coordinate separate calls to document retrieval and GitHub MCP.

A complete answer should establish that:

- Mapayça Markets requires CSV and rejects JSON, based on the pilot requirements.
- Cocoarynth Trace currently exports JSON, based on the implementation or merged pull request.
- The open CSV-support issue tracks the missing work.
- The existing export fields largely align with the pilot and data-sharing policy.

## 6. Check your understanding

Before continuing, make sure you can answer:

1. Which integration establishes that Mapayça Markets requires CSV?
2. Which integration establishes that Cocoarynth Trace currently exports JSON?
3. What work remains before the pilot can use the export?
4. Which tool calls came from the document retrieval server and which came from GitHub MCP?
5. Who coordinated retrieval across the two separate integrations in this exercise?

<!-- markdownlint-disable MD033 -->
<details>
<summary>Check your answers</summary>

- The document retrieval server supplies the Mapayça Markets CSV requirement.
- GitHub MCP and the local repository supply the current JSON implementation evidence.
- Cocoarynth must implement valid CSV generation while retaining the approved field allowlist and other pilot requirements.
- Tool names and server names distinguish document retrieval calls from GitHub calls.
- Copilot coordinated the two integrations in this exercise.

</details>
<!-- markdownlint-enable MD033 -->

[Continue to Exercise 4](exercise4.md) | [Return to the workshop overview](README.md) | [Review Exercise 2](exercise2.md)
