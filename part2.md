# Part 2: Connect Copilot to GitHub

In this part, you will enable GitHub MCP. MCP gives Copilot tools for retrieving live repository content, issues, pull requests, and discussions.

## Contents

- [1. Set up GitHub MCP](#1-set-up-github-mcp)
- [2. Start a fresh chat](#2-start-a-fresh-chat)
- [3. Ask focused follow-up questions](#3-ask-focused-follow-up-questions)
- [4. Compare local and GitHub evidence](#4-compare-local-and-github-evidence)
- [5. Check your understanding](#5-check-your-understanding)
- [Troubleshooting](#troubleshooting)

## 1. Set up GitHub MCP

If the instructor has already configured a server named `github`, skip to the next section.

Follow the instructions for the Copilot client you selected in Part 1.

### Option A: Configure GitHub MCP in VS Code

1. Create or open `.vscode/mcp.json` in the local checkout.
2. Add this configuration:

   ```json
   {
     "servers": {
       "github": {
         "type": "http",
         "url": "https://api.githubcopilot.com/mcp/readonly",
         "headers": {
           "X-MCP-Toolsets": "repos,issues,pull_requests,discussions"
         }
       }
     }
   }
   ```

3. Save the file.
4. Select **Start** above the `github` server definition, or run **MCP: List Servers** from the Command Palette and start `github`.
5. Complete the GitHub authorization prompt with the event-provided account.
6. Confirm that VS Code reports the server as running.
7. In the Copilot Chat panel, select the tools icon and confirm that tools from the `github` server are listed.

Do not commit `.vscode/mcp.json` or push changes from the lab checkout.

### Option B: Configure GitHub MCP in Copilot CLI

The GitHub MCP server comes pre-installed in Copilot CLI with read-only tools enabled by default. Start a new session and add the Discussions toolset:

```shell
copilot --add-github-mcp-toolset discussions
```

From the active Copilot CLI session, verify the server:

```text
/mcp show github-mcp-server
```

Confirm that the built-in server is running and includes tools for repositories, issues, pull requests, and discussions.

### Option C: Configure GitHub MCP in Copilot App

1. Open the GitHub Copilot App.
2. Select **Customize** in the sidebar.
3. Select the **MCP** tab.
4. Open the **Add** menu in the top-right corner, then select **MCP Server**.
5. Enter `github` for the server name.
6. Select **HTTP**.
7. Enter `https://api.githubcopilot.com/mcp/readonly` for the URL.
8. Under **Headers**, select **Add header**.
9. Enter `X-MCP-Toolsets` for the header name and `repos,issues,pull_requests,discussions` for its value.
10. Leave the OAuth Client ID and timeout fields at their defaults, then select **Add server**.
11. Complete GitHub authorization with the event-provided account when prompted.
12. Confirm that the server exposes tools for repositories, issues, pull requests, and discussions.

The hosted `/readonly` endpoint and the CLI's built-in defaults prevent GitHub write tools from being exposed.

## 2. Start a fresh chat

Start a new session in your selected client so it is clear which context comes from GitHub MCP. In VS Code, make sure the new chat is in Agent mode. In the Copilot App, start the session from the Cocoarynth Trace project.

Send this prompt:

> Use GitHub MCP to investigate this repository. Why was the Origin Passport export built this way, and what related work remains open? Cite the relevant pull request, issue, and discussion.

Review each requested tool call before allowing it. Pay attention to:

- Which GitHub tools Copilot selects.
- How it finds relevant artifacts among many issues.
- Whether it distinguishes open work from merged work.
- Whether its supporting links point to the repository, issue, pull request, and discussion.

## 3. Ask focused follow-up questions

Use these prompts if you need to inspect the evidence separately:

- “Find the merged pull request that introduced Origin Passport downloads. What rationale does it give for the chosen format?”
- “Find the open issue about another Origin Passport download format. Summarize its acceptance criteria and current state.”
- “Find the discussion about sharing origin details with wholesale partners. Which fields did the participants agree to include or exclude?”

## 4. Compare local and GitHub evidence

Ask:

> Separate your findings into facts proven by the current code and facts learned from GitHub issues, pull requests, or discussions. Include a link for each GitHub claim.

The current code is the strongest evidence for implemented behavior. An open issue describes planned work, not completed functionality. A merged pull request and discussion can explain rationale that is not obvious from code alone.

## 5. Check your understanding

Before continuing, make sure you can identify:

1. The merged pull request that introduced JSON Origin Passport downloads.
2. Why JSON was selected for the initial implementation.
3. The open issue proposing CSV support.
4. Which partner-facing fields are approved and which internal fields are excluded.
5. Which claims came from local code and which came from live GitHub artifacts.

Do not decide whether the application meets any particular retailer's requirements yet. That question requires organizational documents introduced in a later part of the lab.