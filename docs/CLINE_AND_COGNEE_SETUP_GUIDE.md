# Cline & Cognee: The Developer's Guide to Conversational Coding

**Date:** December 20, 2024
**Status:** The Official Guide for Integrating Your Local VSCode with the Sophia AI Platform

## 1. The Goal: A Seamless Human-AI Development Experience

This guide unlocks the most powerful development workflow for Sophia AI. By following these steps, you will configure **Cline**, the in-editor AI command line, to communicate with:

1.  **A local `cognee` instance:** An MCP server that transforms your local Sophia AI codebase into a queryable knowledge graph.
2.  **The remote, deployed MCP servers:** The full suite of production tools (Pulumi, Kubernetes, GitHub, etc.) running in our EKS cluster.

This creates a unified environment where you can ask deep, contextual questions about your local code and command the entire production infrastructure, all without leaving your editor.

---

## 2. Prerequisites

-   You have completed the [Local Development & Testing Guide](./LOCAL_DEVELOPMENT_GUIDE.md) and have Docker and the `esc` CLI installed and configured.
-   You have **VSCode** installed.
-   You have `git` and `uv` (a Python package installer) installed. `pip install uv`.

---

## 3. Step-by-Step Configuration

### Step 3.1: Install Cline for VSCode

1.  Open VSCode.
2.  Go to the Extensions Marketplace.
3.  Search for and install **"Cline (pre-release)"**.
4.  Reload VSCode when prompted. You should now see a "Cline" icon in your activity bar.

### Step 3.2: Set Up the `cognee` Knowledge Graph Engine

`cognee` is the magic that understands our codebase. We will clone it and set it up locally.

1.  **Clone the Repository:**
    ```bash
    git clone https://www.github.com/topoteretes/cognee
    ```

2.  **Install Dependencies:**
    ```bash
    cd cognee/cognee-mcp
    uv sync --reinstall
    ```

3.  **Activate the Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
    *(Leave this terminal window open and activated for later)*

### Step 3.3: Configure Cline to Find Your MCP Servers

This is the most critical step. We need to tell Cline where to find both the local `cognee` server and our remote, deployed servers.

1.  **Find Your Cline Settings File:**
    -   In VSCode, open the Command Palette (`Cmd+Shift+P` on Mac, `Ctrl+Shift+P` on Windows).
    -   Type `> Cline: Open MCP Settings` and press Enter.
    -   This will open your `cline_mcp_settings.json` file.

2.  **Add the Server Configurations:**
    -   Paste the following JSON into the file.
    -   **You must replace `{CLONE_PATH_TO_COGNEE}`** with the absolute path to the `cognee` directory you cloned in the previous step.

    ```json
    {
      "mcpServers": {
        "cognee": {
          "command": "uv",
          "args": [
            "--directory",
            "/{CLONE_PATH_TO_COGNEE}/cognee-mcp",
            "run",
            "cognee"
          ],
          "env": {
            "ENV": "local",
            "TOKENIZERS_PARALLELISM": "false",
            "LLM_API_KEY": "${env:OPENAI_API_KEY}"
          }
        },
        "pulumi_remote": {
          "url": "http://pulumi-mcp-service.mcp-servers.svc.cluster.local:9000",
          "description": "Interface to the production Pulumi deployment server."
        },
        "k8s_remote": {
          "url": "http://k8s-mcp-service.mcp-servers.svc.cluster.local:9000",
          "description": "Interface to the production Kubernetes cluster."
        },
        "github_remote": {
          "url": "http://github-mcp-service.mcp-servers.svc.cluster.local:9000",
          "description": "Interface to the production GitHub project management server."
        }
      }
    }
    ```

3.  **A Note on Secrets:** Notice the `LLM_API_KEY` for `cognee` is set to `${env:OPENAI_API_KEY}`. Cline is smart enough to use environment variables. To make this work, **you must launch VSCode from a terminal that has been initialized with our secrets**:

    ```bash
    # In your terminal, from the root of the sophia-main project
    esc run scoobyjava-org/default/sophia-ai-production -- code .
    ```
    This command opens VSCode with all our production secrets loaded into its environment, which Cline can then pass to the `cognee` server.

4.  **Restart Cline:** Open the Command Palette again (`Cmd+Shift+P`) and run `> Cline: Restart`.

### Step 3.4: Build Your Code's Knowledge Graph

Now, you will instruct `cognee` to analyze the Sophia AI codebase and build its knowledge graph.

1.  **Open Cline:** Click the Cline icon in the VSCode activity bar.
2.  **Run the `codify` command:** In the Cline input, type the following command, replacing `{PATH_TO_SOPHIA_MAIN}` with the absolute path to this repository, and press Enter.

    ```
    @cognee /codify --path /{PATH_TO_SOPHIA_MAIN}/backend
    ```

3.  **Wait for Processing:** You will see logs from the `cognee` server in the VSCode terminal. This process can take several minutes as it reads all files, generates embeddings, and builds the relational graph.

---

## 4. The Conversational Workflow: You Are Now an AI-Powered Developer

You are now fully set up. Here is how you can use this system:

**Example 1: Understand Local Code**

> `@cognee What is the purpose of the 'MCPOrchestrator' class and how does it relate to the 'mcp_client'?`

`cognee` will use its knowledge graph to provide a detailed, accurate answer about the relationships and functionality within your local code.

**Example 2: Interact with Production Infrastructure**

> `@pulumi_remote Preview the 'production' stack for the 'sophia-ai-agents' project.`

Cline will securely route this request to the deployed Pulumi MCP server, which will execute the command and stream the results back to your editor.

**Example 3: A Multi-Modal Workflow**

> `@cognee Show me the code for the 'AgnoAgentDeployment' component. Then, @k8s_remote tell me how many replicas of that agent are currently running.`

This demonstrates the true power of the system: seamless conversation that pivots between local code understanding and live production infrastructure management.

---

## Conclusion

By following this guide, you have bridged your local development environment directly into the heart of the Sophia AI platform. This unified, conversational interface dramatically enhances productivity, simplifies complex tasks, and represents the future of AI-assisted software development.
