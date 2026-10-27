# Exercise 1: Meet the project

In this exercise, Copilot has access to the project code but not the project's live issues, pull requests, or discussions.

## Contents

- [1. Log in to GitHub](#1-log-in-to-github)
- [2. Set up GitHub Copilot](#2-set-up-github-copilot)
- [3. Ask about the local repository](#3-ask-about-the-local-repository)
- [Bonus: Run the application](#bonus-run-the-application)

## 1. Log in to GitHub

You will use a GitHub account specifically set up for GitHub Universe.

1. Open Microsoft Edge from the taskbar or desktop.
2. Navigate to [https://github.com/ghuni-ldr-1716-w-01](https://github.com/ghuni-ldr-1716-w-01).
3. Select **Sign in** and use the event-provided GitHub account (email/password).
4. Select your profile picture in the upper-right corner and confirm that the displayed username belongs to the event-provided account.
5. Open [ghuni-ldr-1716-w-01/cocoarynth-trace](https://github.com/ghuni-ldr-1716-w-01/cocoarynth-trace) and confirm that you can access the repository.

## 2. Set up GitHub Copilot

Set up one of the GitHub Copilot options below. You will use the same option throughout the workshop.

### Option A: Set up GitHub Copilot App

1. Open the GitHub Copilot App.
2. If prompted, select **Sign in with GitHub** and authenticate with the event-provided GitHub account.
3. From **Projects** in the sidebar, select **+**, then select **Add GitHub repository**.
4. Enter this repository URL: `https://github.com/ghuni-ldr-1716-w-01/cocoarynth-trace`.
5. Start a session for the project and send `Hello` to confirm the agent is working.

### Option B: Set up GitHub Copilot CLI

1. Open a terminal.
2. Run `gh auth login` and follow the prompts to sign in.
3. Run `gh repo clone ghuni-ldr-1716-w-01/cocoarynth-trace` to clone the repository.
4. Run `cd cocoarynth-trace` to enter its directory.
5. Run `copilot` to start GitHub Copilot CLI.
6. If prompted, use `/login` and authenticate with the event-provided GitHub account.
7. When asked to "Confirm folder trust", say "Yes, and remember this folder for future sessions".
8. Send `Hello` to confirm the agent is working.

### Option C: Set up GitHub Copilot in VS Code

1. Open VS Code from the desktop.
2. On the Welcome page, select **Clone Git Repository**.
3. Paste in the URL `https://github.com/ghuni-ldr-1716-w-01/cocoarynth-trace` and press Enter.
4. Choose a local folder for the checkout.
5. When the "Connect to GitHub" dialog pops up, select **Sign in with your browser**.
6. In the consent screen that pops up, authorize **git-ecosystem** to grant access to your GitHub data.
7. When cloning finishes, select **Open** to open the repository in the current window.
8. In the upper right, select the blue **Sign In** button to sign in to GitHub Copilot.
9. A **Restricted Mode** banner appears at the top of the window. Select **Manage** in that banner, and then select **Trust** to trust the folder.
10. In the "Sign in to use GitHub Copilot" dialog, select **Continue with GitHub**.
11. In the browser screen to **Authorize Visual Studio Code**, select **Continue** and then **Authorize Visual-Studio-Code**.
12. Check whether the Chat side panel is open. If it is not, select the **Toggle Chat** icon at the top of VS Code.
13. Make sure the chat is in **Agent** mode. You may see a loop icon that displays **Agent** when selected.
14. Send `Hello` to confirm the agent is working.
15. Below the text box, confirm that **Allow all** is selected so the agent can make tool calls without asking for approval. If it is not, select it.

## 3. Ask about the local repository

Send this prompt:

> Using the implementation files and tests, explain what this project does, identify its main components, and describe how it exports an Origin Passport. Cite the files that support your answer.

Watch how Copilot searches the project. Inspect its tool calls when possible and note which files it uses as evidence. Review requested tool permissions before allowing them.

### Check your understanding

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

## Bonus: Run the application

This exercise is optional. It requires a current Node.js installation.

### Option 1: Ask Copilot to start the application

Send this prompt:

> Install the project dependencies and start the application. Tell me the local URL when it is ready.

Review requested tool permissions before allowing them, or select "Allow all" in the agent field.

If a dialog pops up requesting network access for Node, allow it.

When Copilot confirms that the application is running, continue to [export an Origin Passport](#export-an-origin-passport).

### Option 2: Start the application manually

If Copilot cannot start the application, use this fallback:

1. Open a terminal in the cloned `cocoarynth-trace` repository. If Copilot CLI is running in your current terminal, open a second terminal.
2. Install the dependencies:

    ```shell
    npm ci
    ```

3. Start the React frontend and Express API:

    ```shell
    npm run dev
    ```

### Export an Origin Passport

1. Open `http://localhost:5173` in a browser.
2. Select the shipped batch **ESM-2026-042**.
3. Select **Download JSON** in the Origin Passport section.
4. Open `origin-passport-ESM-2026-042.json` and compare its fields with the internal information shown in the application.
5. Stop the application. Ask Copilot to stop it if Copilot started it, or return to the terminal and press **Control+C** if you started it manually.

Stop here until the instructor introduces Exercise 2.

[Return to the workshop overview](README.md) | [Continue to Exercise 2](exercise2.md)
