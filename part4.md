# Part 4: Create a grounded product requirements document

In this part, you will connect GitHub Copilot to a knowledge base that combines project requirements with Cocoarynth engineering practices. You will keep direct GitHub MCP enabled, then use both integrations to create a local product requirements document (PRD) for CSV Origin Passport support.

## Contents

- [1. Explore the combined knowledge base](#1-explore-the-combined-knowledge-base)
- [2. Get the connection details](#2-get-the-connection-details)
- [3. Connect GitHub Copilot](#3-connect-github-copilot)
- [4. Create the PRD](#4-create-the-prd)
- [5. Review the result](#5-review-the-result)
- [6. Check your understanding](#6-check-your-understanding)

## 1. Explore the combined knowledge base

### Inspect the documents

1. Open the workshop portal URL supplied by your instructor.
2. Under **Corpus 2: Engineering practices**, select **Browse documents**.
3. Preview a few of the documents to get a feel for the contents.

### Inspect the chunks

1. Under **Corpus 2: Engineering practices**, select **View document chunks**.
2. Select the document named "cocoarynth-engineering-culture-presentation.pdf", which was originally a PDF presentation.
3. Review the chunks in page order to see how many slides were put into each chunk.

### Search the chunk index

The Foundry IQ search index contains all the document chunks, with vector embeddings for each one.

1. Under **Corpus 2: Engineering practices**, select **Search the index**.
2. Search for `testing review rollout and monitoring standards`.
3. Inspect the matching passages, source documents, page numbers, and relevance scores.

### Call engineering-practices retrieval over MCP

1. Under **Corpus 2: Engineering practices**, select **Call over MCP**.
2. Ask: “What testing, review, rollout, and monitoring standards apply?”
3. Confirm that the first MCP content block contains the evidence array and each remaining block contains one reference, linked by `ref_id`.
4. Compare the evidence with the direct index-search results.

### Inspect the combined knowledge base

A Foundry IQ knowledge base provides a reusable retrieval interface over one or more knowledge sources. The workshop provisions three knowledge bases in a progressive topology:

- `cocoarynth-kb-docs` uses minimal reasoning over only `cocoarynth-documents-index`.
- `cocoarynth-kb-engineering-practices` uses minimal reasoning over only `cocoarynth-engineering-practices-index`.
- `cocoarynth-kb-all` uses low reasoning across both indexes, allowing an LLM to plan retrieval across project requirements and engineering practices.

The first two power the corpus-specific MCP calls you already tried. The third is the combined knowledge base you will use with Copilot.

1. Under **Combined knowledge base**, select **Configuration**.
2. Inspect the top-level knowledge-base configuration and its nested **Knowledge sources**.
3. Confirm that the reasoning effort is `low` and both Search indexes are attached.
4. Under **Combined knowledge base**, select **Query knowledge base**.
5. Ask:

   > What product requirements and company engineering standards should guide CSV Origin Passport support? Cite evidence from both corpora.

6. Review the extracted evidence, references, and activity log.
7. Check whether Foundry IQ searched both indexes. Retrieval planning can select one or both sources based on the question, so source use is not guaranteed.
8. Under **Combined knowledge base**, select **Call over MCP** and ask the same question.
9. Confirm that the first MCP content block contains the evidence array and each remaining block contains one reference, linked by `ref_id`.
10. Compare the MCP content-only result with the richer query response.

## 2. Get the connection details

1. Under **Combined knowledge base**, select **Configuration**.
2. In the top-level configuration table, find **MCP URL** and select **Copy**.
3. Use the same shared Foundry IQ query key supplied for Part 3.

## 3. Connect GitHub Copilot

For this exercise, enable these integrations:

- Direct GitHub MCP server, from Part 2.
- `cocoarynth-combined`, the combined project-requirements and engineering-practices KB.

Disable `cocoarynth-documents` to avoid exposing the project-document index through two tools.

### Option A: Copilot CLI

1. Exit the active interactive Copilot session if one is running.
2. Add the combined KB, replacing both placeholders:

   ```shell
   copilot mcp add --transport http --header "api-key: <SEARCH_QUERY_KEY>" cocoarynth-combined "<COMBINED_KB_MCP_ENDPOINT>"
   ```

3. Start a fresh session with only the documents-only KB disabled:

   ```shell
   copilot --disable-mcp-server cocoarynth-documents --add-github-mcp-toolset discussions
   ```

4. Verify both required servers:

   ```text
   /mcp show github-mcp-server
   /mcp show cocoarynth-combined
   ```

Do not use `--disable-builtin-mcps`; that would disable the direct GitHub integration needed for this exercise.

### Option B: Copilot App

1. Open the GitHub Copilot App.
2. Select **Customize**, then select the **MCP** tab.
3. Open **Add**, then select **MCP Server**.
4. Enter `cocoarynth-combined` for the server name and select **HTTP**.
5. Paste the copied combined KB MCP URL into the URL field.
6. Under **Headers**, add `api-key` with the shared Foundry IQ query key as its value.
7. Leave other fields at their defaults, then select **Add server**.
8. Keep `github` and `cocoarynth-combined` enabled. Disable only `cocoarynth-documents`.

### Option C: VS Code

1. Open `.mcp.json` at the root of the local checkout.
2. Keep the existing `github` server definition and add `cocoarynth-combined` under `servers`:

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
4. Start `github` and `cocoarynth-combined`. Stop only `cocoarynth-documents`.
5. Enter the shared Foundry IQ query key if VS Code prompts for it.
6. In Copilot Chat, select the tools icon and confirm that tools from GitHub and the combined KB are available.

Do not commit `.mcp.json` or push changes from the lab checkout.

## 4. Create the PRD

Start a fresh chat so earlier answers do not supply hidden context. In VS Code, use Agent mode. In the Copilot App, start from the Cocoarynth Trace project.

Send this prompt:

> Create a local Markdown file named `origin-passport-csv-prd.md` containing a product requirements document for adding CSV Origin Passport export support to Cocoarynth Trace. Before drafting, retrieve evidence from both direct GitHub MCP and `cocoarynth-combined`. Use GitHub for current code, issues, pull requests, and discussions. Use the combined knowledge base for project requirements, architecture, policy, support constraints, and company engineering standards. Address Mapayça Markets' CSV requirement and rejection of JSON, and whether CSV export must preserve the immutable Origin Passport snapshot. Distinguish required behavior, current implementation, and recommendations. Include context, goals, non-goals, user stories, API and export contract, UI and accessibility requirements, implementation considerations, acceptance criteria, testing, rollout and observability, open questions, and source links. Do not modify application code or any GitHub artifact. Do not finish until the Markdown file has been created.

Approve read-only tool calls and the creation of the one local Markdown file. Reject any request to change application code or write to GitHub.

After Copilot finishes, open `origin-passport-csv-prd.md` in the local checkout.

## 5. Review the result

Check the PRD against the evidence. It should:

- State that Mapayça Markets accepts CSV and rejects JSON.
- Preserve the immutable Origin Passport snapshot rather than rebuilding historical values.
- Describe UTF-8 CSV, the required stable headers, standard quoting, empty optional fields, filename, and `text/csv` response behavior.
- Treat current JSON export and open CSV work as implementation facts supported by GitHub evidence.
- Keep bulk export outside the pilot scope.
- Exclude confidential, personal, and unapproved fields.
- Apply Cocoarynth's API contract, React and TypeScript, UI, accessibility, testing, review, rollout, and monitoring standards where relevant.
- Separate sourced requirements from Copilot's recommendations and list unresolved questions honestly.
- Link to the relevant GitHub artifacts and identify the supporting indexed documents or guides.

Inspect the chat's tool activity as well as the finished file:

| Coordination layer | Responsibility |
| --- | --- |
| Foundry IQ | Plans retrieval across the project-requirements and engineering-practices indexes inside `cocoarynth-combined`. |
| GitHub Copilot | Coordinates the combined KB with direct GitHub MCP and the local workspace. |
| Direct GitHub MCP | Retrieves live repository evidence using the attendee's GitHub authorization. |

If the PRD lacks evidence from one source, ask Copilot to retrieve that source explicitly and revise the file. Do not accept a polished document as grounded merely because it sounds plausible.

## 6. Check your understanding

Before finishing, make sure you can answer:

1. Which two indexes are children of `cocoarynth-kb-all`?
2. Why did you disable `cocoarynth-documents` but keep direct GitHub MCP enabled?
3. What retrieval does Foundry IQ coordinate, and what retrieval does Copilot coordinate?
4. Why might the combined KB use only one index for a particular question?
5. Which identity is used for direct GitHub retrieval?
6. Why should the PRD distinguish requirements, current behavior, and recommendations?

<!-- markdownlint-disable MD033 -->
<details>
<summary>Check your answers</summary>

- The combined KB contains `cocoarynth-documents-index` and `cocoarynth-engineering-practices-index`, exposed through their Search Index knowledge sources.
- Disabling the documents-only KB prevents duplicate access to the same project-document index. GitHub remains enabled because it is a separate source of live implementation and planning evidence.
- Foundry IQ plans across the two Search indexes inside the combined KB. Copilot coordinates the combined KB, direct GitHub MCP, and the local workspace.
- Retrieval planning selects sources relevant to the question and does not guarantee that every source will be searched.
- Direct GitHub MCP uses the attendee's event-provided GitHub account.
- The distinction prevents a current limitation or generated suggestion from being mistaken for an approved product requirement.

</details>
<!-- markdownlint-enable MD033 -->

[Return to the lab overview](README.md) | [Review Part 3](part3.md)
