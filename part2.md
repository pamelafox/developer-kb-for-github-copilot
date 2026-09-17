# Part 2: Connect Copilot to GitHub

In this part, you will explore the project's live GitHub artifacts in your browser, then enable GitHub MCP. MCP gives Copilot tools for retrieving repository content, issues, pull requests, and discussions.

## Contents

- [1. Explore the repository on GitHub](#1-explore-the-repository-on-github)
- [2. Set up GitHub MCP](#2-set-up-github-mcp)
- [3. Investigate with GitHub MCP](#3-investigate-with-github-mcp)
- [Bonus: Trace the feature's history](#bonus-trace-the-features-history)

## 1. Explore the repository on GitHub

### Confirm your GitHub account

1. Return to [pamelafox/cocoarynth-trace](https://github.com/pamelafox/cocoarynth-trace) in your browser.
2. Select your profile picture in the upper-right corner and confirm that you are still signed in with the event-provided account from Part 1.
3. If GitHub shows a not-found or access error, ask your instructor to verify your account before continuing.

Use the same GitHub account when a Copilot client asks you to authorize GitHub MCP later in this part.

### Browse the project activity

Explore the repository before asking Copilot to investigate it:

1. On the **Code** tab, scan the repository files and README.
2. Open the **Issues** tab. Look at both open and closed issues, noting their titles, labels, and status.
3. Open the **Pull requests** tab. Look at open, closed, and merged pull requests, and open one to inspect its description and changed files.
4. Open the **Discussions** tab. Browse the categories and open a discussion to see how decisions and context are recorded.
5. Notice which artifacts describe current code, completed work, proposed work, and team decisions.

Do not create, edit, close, or comment on any GitHub artifact. You will ask Copilot to find the relevant evidence after GitHub MCP is connected.

## 2. Set up GitHub MCP

If the instructor has already configured a server named `github`, skip to the next section.

Follow the instructions for the Copilot client you selected in Part 1.

### Option A: Configure GitHub MCP in VS Code

1. Create or open `.mcp.json` at the root of the local checkout.
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

Do not commit `.mcp.json` or push changes from the lab checkout.

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

## 3. Investigate with GitHub MCP

### Start a fresh chat

Start a new session in your selected client so it is clear which context comes from GitHub MCP. In VS Code, make sure the new chat is in Agent mode. In the Copilot App, start the session from the Cocoarynth Trace project.

Send this prompt:

> Use GitHub MCP to investigate this repository. Why was the Origin Passport export built this way, and what related work remains open? Cite the relevant pull request, issue, and discussion.

Review each requested tool call before allowing it. Pay attention to:

- Which GitHub tools Copilot selects.
- How it finds relevant artifacts among many issues.
- Whether it distinguishes open work from merged work.
- Whether its supporting links point to the repository, issue, pull request, and discussion.

### Check your understanding

Before continuing, make sure you can identify:

1. The merged pull request that introduced JSON Origin Passport downloads.
2. Why JSON was selected for the initial implementation.
3. The open issue proposing CSV support.
4. Which partner-facing fields are approved and which internal fields are excluded.
5. Which claims came from local code and which came from live GitHub artifacts.

<!-- markdownlint-disable MD033 -->
<details>
<summary>Check your answers</summary>

- The merged pull request **Add downloadable Origin Passports for production batches** introduced the JSON download.
- JSON was selected because the feature began as an internal API integration.
- An open issue proposes CSV downloads; it describes planned work, not implemented behavior.
- The approved partner-facing fields cover batch identity, origin, harvest, production, quality, and shipment facts. Internal notes, costs, supplier contacts, and operational metadata remain excluded.
- The implementation files prove the application's current behavior. The merged pull request explains the JSON decision, the open issue tracks CSV work, and the discussion records which fields may be shared.

</details>
<!-- markdownlint-enable MD033 -->

Do not decide whether the application meets any particular retailer's requirements yet. That question requires organizational documents introduced in a later part of the lab.

## Bonus: Trace the feature's history

This exercise is optional. Ask Copilot:

> Use GitHub MCP to reconstruct the history of the Origin Passport export. Create a timeline using relevant commits, pull requests, issues, and discussions. For each event, include its date, status, link, and what changed or was decided.

Check that the timeline:

- Distinguishes merged work from open proposals.
- Uses direct links to every GitHub artifact.
- Explains how discussions influenced implementation.
- Does not claim that planned CSV support is complete.

[Return to the lab overview](README.md) | [Continue to Part 3](part3.md)
