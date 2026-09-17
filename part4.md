# Part 4: Use the combined knowledge base

In this part, you will connect GitHub Copilot to a knowledge base that combines the indexed Cocoarynth documents with live GitHub tools, then compare this approach with the separate integrations from Part 3.

## Contents

- [1. Explore the combined knowledge base](#1-explore-the-combined-knowledge-base)
- [2. Get the connection details](#2-get-the-connection-details)
- [3. Connect GitHub Copilot to the combined knowledge base](#3-connect-github-copilot-to-the-combined-knowledge-base)
- [4. Start an isolated comparison chat](#4-start-an-isolated-comparison-chat)
- [5. Compare the results](#5-compare-the-results)
- [6. Check your understanding](#6-check-your-understanding)

## 1. Explore the combined knowledge base

The combined knowledge base, `cocoarynth-kb-all`, has two knowledge sources:

- `cocoarynth-documents-source` searches the indexed workshop documents.
- `cocoarynth-github-source` uses read-only GitHub MCP tools to retrieve live repository evidence.

Foundry IQ plans retrieval across both sources behind one MCP endpoint. The GitHub knowledge source uses an instructor-managed read-only lab identity; attendees do not receive or enter its credential.

1. Open the workshop portal URL supplied by your instructor.
2. Open **Combined knowledge base**.
3. Inspect the top-level knowledge-base configuration and its nested **Knowledge sources**.
4. Confirm that one source has the kind `searchIndex` and the other has the kind `mcpServer`.
5. Ask: “Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker, check relevant issues for related open work, and cite both the pilot requirements and current implementation evidence.”
6. Review the extracted evidence, references, and activity log. Check what queries Foundry IQ sent to the search index, and what tool calls it made to the GitHub MCP server. A combined knowledge base *can* use both sources, but it does not guarantee that every source will be selected for every question.

## 2. Get the connection details

1. In **Combined knowledge base**, find the `cocoarynth-kb-all` configuration.
2. In the top-level configuration table, find **MCP URL** and select **Copy**.
3. Use the same shared Foundry IQ query key supplied for Part 3.

## 3. Connect GitHub Copilot to the combined knowledge base

Follow the instructions for the Copilot client you selected in Part 1.

### Option A: Configure the combined knowledge base in Copilot CLI

1. Exit the active interactive Copilot session if one is running.
2. Run the following command, replacing both placeholders with the values supplied for the lab:

   ```shell
   copilot mcp add --transport http --header "api-key: <SEARCH_QUERY_KEY>" cocoarynth-combined "<COMBINED_KB_MCP_ENDPOINT>"
   ```

3. Start a comparison session with the built-in GitHub MCP server and the documents-only knowledge base disabled:

   ```shell
   copilot --disable-builtin-mcps --disable-mcp-server cocoarynth-documents
   ```

4. Verify the combined server:

   ```text
   /mcp show cocoarynth-combined
   ```

5. Confirm that `cocoarynth-combined` is running.

The disable flags apply to this Copilot CLI session; they do not delete either existing server configuration.

### Option B: Configure the combined knowledge base in Copilot App

1. Open the GitHub Copilot App.
2. Select **Customize** in the sidebar, then select the **MCP** tab.
3. Open the **Add** menu, then select **MCP Server**.
4. Enter `cocoarynth-combined` for the server name and select **HTTP**.
5. Paste the copied combined KB MCP URL into the URL field.
6. Under **Headers**, add `api-key` with the shared Foundry IQ query key as its value.
7. Leave other fields at their defaults, then select **Add server**.
8. Disable `github` and `cocoarynth-documents` for the comparison, leaving only `cocoarynth-combined` enabled.
9. Confirm that `cocoarynth-combined` is available.

### Option C: Configure the combined knowledge base in VS Code

1. Open `.mcp.json` at the root of the local checkout.
2. Keep the existing server definitions and add `cocoarynth-combined` under `servers`:

   ```json
   "cocoarynth-combined": {
     "type": "http",
     "url": "<COMBINED_KB_MCP_ENDPOINT>",
     "headers": {
       "api-key": "${input:cocoarynth-search-key}"
     }
   }
   ```

3. Replace `<COMBINED_KB_MCP_ENDPOINT>` with the endpoint copied from the workshop portal, then save the file.
4. Select **Start** above `cocoarynth-combined`, or run **MCP: List Servers** from the Command Palette and start it.
5. Enter the shared Foundry IQ query key if VS Code prompts for it.
6. Run **MCP: List Servers** and stop `github` and `cocoarynth-documents` for the comparison.
7. Confirm that `cocoarynth-combined` is running and the two separate servers are stopped.
8. In Copilot Chat, select the tools icon and confirm that the combined knowledge-base tool is available.

Do not commit `.mcp.json` or push changes from the lab checkout.

## 4. Start an isolated comparison chat

Start a fresh chat so the earlier conversation does not influence the comparison. In VS Code, make sure the chat is in Agent mode. In the Copilot App, start the session from the Cocoarynth Trace project.

Only `cocoarynth-combined` should be enabled for this exercise. Disabling the separate GitHub and documents-only servers ensures that evidence from both sources is retrieved through the combined knowledge base rather than coordinated directly by Copilot.

Send the same question used in Part 3:

> Can Cocoarynth support Mapayça Markets' traceability import today? Identify the blocker, check relevant issues for related open work, and cite both the pilot requirements and current implementation evidence.

Expand the `knowledge_base_retrieve` tool call and inspect the query sent to the combined knowledge base.

## 5. Compare the results

Check whether the response:

- Establishes that Mapayça Markets requires CSV and rejects JSON.
- Establishes that Cocoarynth Trace currently exports JSON.
- Identifies the open CSV-support issue as planned work, not implemented behavior.
- Attributes requirements and implementation evidence to the appropriate sources.
- Expresses uncertainty if one source was not retrieved.

Compare the activity with Part 3:

| Part 3: Separate integrations | Part 4: Combined knowledge base |
| --- | --- |
| Copilot chooses between the documents KB and GitHub MCP tools. | Copilot calls one combined KB tool. |
| Copilot coordinates separate retrieval calls. | Foundry IQ plans retrieval across document and GitHub knowledge sources. |
| GitHub MCP uses the attendee's GitHub authentication. | The GitHub knowledge source uses the instructor-managed read-only lab identity. |

The combined knowledge base is a reusable retrieval configuration, not a promise of a better answer. Judge the result by its evidence, attribution, and treatment of uncertainty.

## 6. Check your understanding

Before finishing, make sure you can answer:

1. Which two knowledge sources are children of `cocoarynth-kb-all`?
2. Why did you disable the separate GitHub and documents-only integrations?
3. Who coordinated retrieval in Part 3, and who coordinated it in Part 4?
4. Why might a combined knowledge base use only one source for a particular question?
5. Which GitHub identity does the combined knowledge base use?

<!-- markdownlint-disable MD033 -->
<details>
<summary>Check your answers</summary>

- The combined KB contains the document search-index source and the GitHub MCP source.
- Disabling the separate integrations isolates retrieval through the combined endpoint and makes the comparison meaningful.
- Copilot coordinated separate integrations in Part 3; Foundry IQ plans across the combined KB's sources in Part 4.
- Retrieval planning selects sources relevant to the question and does not guarantee every source will be called.
- The combined KB uses the instructor-managed read-only lab identity stored in the GitHub knowledge source.

</details>
<!-- markdownlint-enable MD033 -->

[Return to the lab overview](README.md) | [Review Part 3](part3.md)
