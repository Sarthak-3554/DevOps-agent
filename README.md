# devops-agent

A CLI tool that lets you talk to Git and your terminal in plain English.
Instead of remembering commands, just say what you want:

```
> push my changes to main
> what's my git status?
> install git and stage my changes
```

The agent figures out which command to run and does it for you.

## How it works

1. You type a request in plain English.
2. An LLM decides which tool to use (git push, git status, run a shell
   command, etc.) and with what arguments.
3. The tool runs, and the result is shown to you.
4. If something fails, the agent tries to fix it and retry — automatically.

## Features

- **Natural language commands** — no need to memorize git or shell syntax.
- **Safe by default** — anything risky (like `git push` or an unrecognized
  shell command) asks for your confirmation before running.
- **Sandboxed shell** — shell commands run inside an isolated Docker
  container, not directly on your computer. So even if something goes
  wrong, it can't damage your actual machine.
- **Self-correcting** — if a command fails, the agent reads the error and
  tries a fix on its own.
- **Works with multiple AI providers** — OpenAI, Groq, Anthropic, etc. Just
  change one line in the config.
  
## Audit logging

Every LLM call and tool execution is logged as structured JSON (one
object per line) to `storage/logs/audit.jsonl` — this is a permanent,
queryable record, since terminal output disappears once a session ends.
Each entry is tagged with a `session_id` shared across all calls within
one `agent.run()` invocation, so a single user request's full trace
(every LLM call, every tool call, confirmation given or denied, success/
failure, latency) can be reconstructed after the fact. Logging lives
inside `Executor.execute()` rather than the caller, since that's where
confirmation details actually exist.

## Setup

**1. Install dependencies**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Add your API key**

Copy `.env.example` to `.env` and fill in your model + API key:
```
MODEL=groq/openai/gpt-oss-120b
GROQ_API_KEY=your_key_here
```

**3. Build the sandbox** (one-time setup)
```bash
docker build -t devops-agent-sandbox:latest -f Dockerfile.sandbox .
```
This creates the isolated container that shell commands will run inside.
Make sure Docker Desktop is installed and running first.

**4. Run it**
```bash
python3 main.py
```

Then just type what you want:
```
> git status
> push my changes to main
```

## What's not done yet

- No automated test suite that scores the agent's accuracy — just manual
  testing and unit tests so far.
- No memory between separate runs — each time you start `main.py`, it
  starts fresh.
