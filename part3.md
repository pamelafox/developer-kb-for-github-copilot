# Part 3: Connect GitHub Copilot to document retrieval

In this part, you will explore Cocoarynth's pre-ingested document collection, test retrieval over MCP in the workshop portal, and connect GitHub Copilot to the document retrieval server.

## Contents

- [1. Explore the document corpus](#1-explore-the-document-corpus)
- [2. Get the connection details](#2-get-the-connection-details)
- [3. Connect GitHub Copilot](#3-connect-github-copilot)
- [4. Start a fresh chat](#4-start-a-fresh-chat)
- [5. Test document retrieval](#5-test-document-retrieval)
- [6. Combine document and GitHub evidence](#6-combine-document-and-github-evidence)
- [7. Check your understanding](#7-check-your-understanding)

## 1. Explore the document corpus

Your instructor has already indexed Cocoarynth documents into a Foundry IQ service using an Azure account. Since you do not have Azure accounts in this workshop, you will explore the Foundry IQ service using a special portal. If you're curious to see the code that ingested the documents, check out [foundry_iq.py](app/backend/foundry_iq.py).

### Inspect the documents

The Cocoarynth documents are stored in Azure Blob Storage. These documents contain organizational context that is not available from application code or the GitHub repository.

1. Open the workshop portal URL supplied by your instructor.
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

## 2. Get the connection details

1. Under **Corpus 1: Project requirements**, select **Call over MCP**.
2. Next to **MCP endpoint**, select **Copy**.
3. Get the shared Foundry IQ query key through the private method specified by your instructor. The query key is a shared lab credential. Do not paste the key into chat, commit it to the repository, include it in screenshots, or share it with anyone outside the lab.

## 3. Connect GitHub Copilot

Follow the instructions for the Copilot client you selected in Part 1. Name this connection `cocoarynth-documents` so it is easy to distinguish from GitHub MCP and the combined retrieval server used later.

### Option A: Configure the MCP server in Copilot CLI

1. Exit the active interactive Copilot session if one is running.
2. Run the following command, replacing both placeholders with the values supplied for the lab:

   ```shell
   copilot mcp add --transport http --header "api-key: <SEARCH_QUERY_KEY>" cocoarynth-documents "<DOCUMENTS_KB_MCP_ENDPOINT>"
   ```

3. Start a new Copilot CLI session:

   ```shell
   copilot
   ```

4. Verify the new server:

   ```text
   /mcp show cocoarynth-documents
   ```

5. Confirm that `cocoarynth-documents` and the built-in GitHub MCP server are both running.

### Option B: Configure the MCP server in Copilot App

1. Open the GitHub Copilot App.
2. Select **Customize** in the sidebar.
3. Select the **MCP** tab.
4. Open the **Add** menu, then select **MCP Server**.
5. Enter `cocoarynth-documents` for the server name.
6. Select **HTTP**.
7. Paste the copied MCP URL into the URL field.
8. Under **Headers**, select **Add header**.
9. Enter `api-key` for the header name and the Search query key for its value.
10. Leave other fields at their defaults, then select **Add server**.
11. Confirm that `github` and `cocoarynth-documents` are both available.

### Option C: Configure the MCP server in VS Code

1. Open `.mcp.json` at the root of the local checkout.
2. Keep the existing `github` server and add the `cocoarynth-documents` server and secure input shown below.
3. Replace `<DOCUMENTS_KB_MCP_ENDPOINT>` with the endpoint copied from the workshop portal.

   ```json
   {
     "inputs": [
       {
         "id": "cocoarynth-search-key",
         "type": "promptString",
         "description": "Cocoarynth lab Search query key",
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
       "cocoarynth-documents": {
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
5. Select **Start** above `cocoarynth-documents`, or run **MCP: List Servers** from the Command Palette and start it.
6. Enter the Search query key when VS Code prompts for it.
7. Confirm that both `github` and `cocoarynth-documents` are running.
8. In Copilot Chat, select the tools icon and confirm that tools from both servers are available.

Do not commit `.mcp.json` or push changes from the lab checkout.

## 4. Start a fresh chat

Start a new session so you can clearly observe which integrations Copilot uses. In VS Code, make sure the chat is in Agent mode. In the Copilot App, start the session from the Cocoarynth Trace project.

Both separate integrations should remain enabled:

- `github` supplies live code, issues, pull requests, and discussions.
- `cocoarynth-documents` supplies the uploaded requirements, policy, architecture decision, and support runbook.

Review each requested tool call before allowing it. The tool or server name tells you which source Copilot is consulting.

## 5. Test document retrieval

First ask a question that can be answered from the uploaded documents:

> What file format does Mapayça Markets require for the Cocoarynth traceability pilot, and does its importer accept JSON? Cite the supporting document.

Check that Copilot:

- Calls a tool from `cocoarynth-documents`. Expand the tool call to see the arguments passed to the `knowledge_base_retrieve` tool.
- Responds that CSV is the required format, not JSON.
- Cites the Mapayça Markets pilot requirements PDF rather than local code or a GitHub issue.

## 6. Combine document and GitHub evidence

Now ask a question that requires both integrations:

> Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker, check relevant issues for related open work (using GitHub MCP), and cite both the pilot requirements and current implementation evidence.

Inspect the tool calls and answer. Copilot should coordinate separate calls to document retrieval and GitHub MCP.

A complete answer should establish that:

- Mapayça Markets requires CSV and rejects JSON, based on the pilot requirements.
- Cocoarynth Trace currently exports JSON, based on the implementation or merged pull request.
- The open CSV-support issue tracks the missing work.
- The existing export fields largely align with the pilot and data-sharing policy.

## 7. Check your understanding

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

[Continue to Part 4](part4.md) | [Return to the lab overview](README.md) | [Review Part 2](part2.md)
