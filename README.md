# AIM-OS (Artificial Intelligence Manager – Operating System)

## Overview

AIM-OS bridges Linux system introspection with large‑language‑model reasoning. It captures real‑time data from the host and lets you administer the machine in plain English requests—no shell scripting required.

## Capabilities at a Glance

* **Natural‑language administration**: ask AIM‑OS to check resources, manage packages, or troubleshoot services with simple English instructions.
* **Real‑time telemetry**: Rust and Bash collectors stream process, network, and hardware metrics directly to the LLM.
* **Secure, deterministic execution**: every action is sandboxed and logged for auditability.
* **Extensible pipeline**: plug‑in collectors and response adapters to tailor AIM‑OS to any Linux distribution or cloud instance.

## Prerequisites

* **Rust**
* **Python 3.9+**

Python packages (install via `pip`):

```bash
rich
aioconsole
python-dotenv
openai
typing_extensions
psutil
```

## Installation

```bash
git clone https://github.com/DCV05/AIM-OS.git
cd AIM-OS
pip install -r requirements.txt
```

## OpenAI Assistant Setup

AIM‑OS communicates with an OpenAI Assistant that follows a strict JSON contract for every response.

1. Open the **Assistants** section in your OpenAI dashboard and create a new assistant.
2. Paste the system prompt provided in `prompts/assistant_system_prompt.md` into the *System instructions* box.
3. Add a *Function* tool and supply the response JSON schema located at `schema/response_schema.json`. The schema enforces the following structure:

```json
{
  "response_type": "text | linux_command",
  "response": ["..."],
  "metacommand": "",
  "error": "",
  "dangerous_command": 0 | 1
}
```

4. Save the assistant and copy its `assistant_id` into your `.env` file.

## Configuration

Create a `.env` file in the project root and supply your OpenAI credentials:

```env
OPENAI_API_KEY=sk-***************************************
ASSISTANT_ID=asst_**************************************
```

## Usage

Start the interactive terminal:

```bash
python main.py
```

When prompted, type requests in natural language, for example:

```
Show me the top 5 processes by memory
Clean the apt cache
How much free disk space do I have on /home?
Create a tar.gz backup of /var/log and store it in /backups
```

AIM‑OS will translate your request into the appropriate shell commands, execute them safely, and return the results in a readable format.

## Roadmap

* Multiple‑model back‑end support (OpenAI, local LLMs)
* Role‑based permission profiles
* Web dashboard
