# Building a developer knowledge base for GitHub Copilot

You are an engineer working for **Cocoarynth**, a fictional single-origin chocolate manufacturer. Your team builds **Cocoarynth Trace**, an application that traces chocolate from cacao harvest through production and shipment.

You will begin with the project code, then connect GitHub Copilot to live GitHub artifacts through GitHub MCP.

These instructions cover:

- **Part 0:** Explore the local repository with GitHub Copilot.
- **Part 1:** Add GitHub MCP and investigate issues, pull requests, and discussions.

You do not need to install dependencies or run the application.

## Before you begin

Confirm that:

- You are signed in to the event-provided GitHub account.
- Your account can open [pamelafox/cocoarynth-trace](https://github.com/pamelafox/cocoarynth-trace) on GitHub.
- At least one of these clients is available: GitHub Copilot in VS Code, GitHub Copilot CLI, or GitHub Copilot App.

The repository is read-only for this lab. Do not create, edit, close, or comment on GitHub artifacts.

## Part 0: Meet the project

In this part, Copilot has access to the project code but not the project's live issues, pull requests, or discussions.

### 1. Set up GitHub Copilot

Set up one of the GitHub Copilot options below. You will use the same option throughout the lab.

#### Option A: Set up GitHub Copilot CLI

1. Open a terminal.
2. Run `gh auth login` and follow the prompts to sign in.
3. Run `gh repo clone pamelafox/cocoarynth-trace` to clone the repository.
4. Run `cd cocoarynth-trace` to enter its directory.
5. Run `copilot` to start GitHub Copilot CLI.
6. If prompted, use `/login` and authenticate with the event-provided GitHub account.
7. When asked to "Confirm folder trust", say "Yes, and remember this folder for future sessions".
8. Send `Hello` to confirm the agent is working.

#### Option B: Set up GitHub Copilot App

1. Open the GitHub Copilot App.
2. If prompted, select **Sign in with GitHub** and authenticate with the event-provided GitHub account.
3. From **Projects** in the sidebar, select **+**, then select **Add GitHub repository**.
4. Enter this repository URL: `https://github.com/pamelafox/cocoarynth-trace`.
5. Start a session for the project and send `Hello` to confirm the agent is working.

#### Option C: Set up GitHub Copilot in VS Code

1. Open a new VS Code window by selecting **File** > **New Window**.
2. On the Welcome page, select **Clone Git Repository**.
3. Select **Clone from GitHub**. If prompted, sign in with the event-provided GitHub account.
4. Enter `pamelafox/cocoarynth-trace` and select the repository from the results.
5. Choose a local folder for the checkout.
6. When cloning finishes, select **Open** to open the repository in the new window.
7. If prompted, confirm that you trust the repository authors.
8. Check whether the Chat side panel is open. If it is not, select the **Toggle Chat** icon at the top of VS Code.
9. Make sure the chat is in **Agent** mode. You may see a loop icon that displays **Agent** when selected.
10. Send `Hello` to confirm the agent is working.

### 2. Ask about the local repository

Send this prompt:

> Using the implementation files and tests, explain what this project does, identify its main components, and describe how it exports an Origin Passport. Cite the files that support your answer.

Watch how Copilot searches the project. Inspect its tool calls when possible and note which files it uses as evidence. Review requested tool permissions before allowing them.

### 3. Check your understanding

1. What does Cocoarynth Trace do?
2. What are the main components of the project?
3. When can the application create an Origin Passport, and which file creates it?
4. What format does the application download, and what information is deliberately excluded?

<!-- markdownlint-disable MD033 -->
<details>
<summary>Check your answers</summary>

- Cocoarynth Trace tracks chocolate production batches from cacao harvest through production and shipment.
- Its main components are a React frontend, Express API, shared types, deterministic fixtures, and tests.
- Shipped batches can produce an Origin Passport. The passport is created in `server/services/originPassport.ts`.
- The application downloads a JSON attachment assembled from an allowlist that excludes internal fields.

</details>
<!-- markdownlint-enable MD033 -->

If Copilot's response does not give you enough evidence to answer these questions, ask focused follow-up questions before continuing.

The local code shows what the application does. It may not explain the product decisions or planned work behind that behavior.

## Part 1: Connect Copilot to GitHub

In this part, you will enable GitHub MCP. MCP gives Copilot tools for retrieving live repository content, issues, pull requests, and discussions.

### 1. Set up GitHub MCP

If the instructor has already configured a server named `github`, skip to the next section.

Follow the instructions for the Copilot client you selected in Part 0.

#### Option A: Configure GitHub MCP in VS Code

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

#### Option B: Configure GitHub MCP in Copilot CLI

The GitHub MCP server comes pre-installed in Copilot CLI with read-only tools enabled by default. Start a new session and add the Discussions toolset:

```shell
copilot --add-github-mcp-toolset discussions
```

From the active Copilot CLI session, verify the server:

```text
/mcp show github-mcp-server
```

Confirm that the built-in server is running and includes tools for repositories, issues, pull requests, and discussions.

#### Option C: Configure GitHub MCP in Copilot App

1. Open the GitHub Copilot App.
2. Select the **Settings** gear in the bottom-left corner.
3. Select **MCP servers** from the settings menu.
4. Select **+ Add server**, then select **Add custom server**.
5. Enter `github` for the server name.
6. Select **HTTP** and enter `https://api.githubcopilot.com/mcp/readonly` for the URL.
7. Select **Add server**.
8. Complete GitHub authorization with the event-provided account when prompted.
9. Confirm that the server exposes tools for repositories, issues, pull requests, and discussions.

The hosted `/readonly` endpoint and the CLI's built-in defaults prevent GitHub write tools from being exposed.

### 2. Start a fresh chat

Start a new session in your selected client so it is clear which context comes from GitHub MCP. In VS Code, make sure the new chat is in Agent mode. In the Copilot App, start the session from the Cocoarynth Trace project.

Send this prompt:

> Use GitHub MCP to investigate `pamelafox/cocoarynth-trace`. Why was the Origin Passport export built this way, and what related work remains open? Cite the relevant pull request, issue, and discussion.

Review each requested tool call before allowing it. Pay attention to:

- Which GitHub tools Copilot selects.
- How it finds relevant artifacts among many issues.
- Whether it distinguishes open work from merged work.
- Whether its supporting links point to the repository, issue, pull request, and discussion.

### 3. Ask focused follow-up questions

Use these prompts if you need to inspect the evidence separately:

- “Find the merged pull request that introduced Origin Passport downloads. What rationale does it give for the chosen format?”
- “Find the open issue about another Origin Passport download format. Summarize its acceptance criteria and current state.”
- “Find the discussion about sharing origin details with wholesale partners. Which fields did the participants agree to include or exclude?”

### 4. Compare local and GitHub evidence

Ask:

> Separate your findings into facts proven by the current code and facts learned from GitHub issues, pull requests, or discussions. Include a link for each GitHub claim.

The current code is the strongest evidence for implemented behavior. An open issue describes planned work, not completed functionality. A merged pull request and discussion can explain rationale that is not obvious from code alone.

### Part 1 checkpoint

Before continuing, make sure you can identify:

1. The merged pull request that introduced JSON Origin Passport downloads.
2. Why JSON was selected for the initial implementation.
3. The open issue proposing CSV support.
4. Which partner-facing fields are approved and which internal fields are excluded.
5. Which claims came from local code and which came from live GitHub artifacts.

Do not decide whether the application meets any particular retailer's requirements yet. That question requires organizational documents introduced in a later part of the lab.

## Troubleshooting

### The GitHub server does not start

- In VS Code, run **MCP: List Servers** and restart `github`.
- In Copilot CLI, run `/mcp show github-mcp-server`.
- In the Copilot App, open **Settings** > **MCP servers** and check `github`.
- For VS Code or the Copilot App, confirm the URL is `https://api.githubcopilot.com/mcp/readonly`.
- Confirm that you authenticated with the event-provided GitHub account.
- Ask an instructor before changing the server configuration.

### Copilot cannot access the repository

Open [pamelafox/cocoarynth-trace](https://github.com/pamelafox/cocoarynth-trace) in your browser while signed in with the same account. If GitHub shows a permission error, ask an instructor to verify repository access.

### Copilot does not use GitHub MCP

Start a fresh session and explicitly begin the prompt with:

> Use GitHub MCP to investigate `pamelafox/cocoarynth-trace`.

Check that the response includes live GitHub links rather than relying only on local files.

### A write action is requested

Deny the request and ask an instructor for help. The configured server should expose only read operations.
