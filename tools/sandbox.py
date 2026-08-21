import os
from typing import Optional

import docker
from docker.errors import DockerException, ImageNotFound
from dotenv import load_dotenv

from models.tool_result import ToolResult

# Load .env here explicitly rather than relying on some other module
# having already done it first. Import order across the codebase isn't
# guaranteed (this module's env reads below were previously executing
# before llm/litellm_provider.py's load_dotenv() call ran, because
# agent/executor.py — which imports this module — is imported before
# llm/factory.py in agent/agent.py). Calling it again here is a no-op
# if already loaded, and safe regardless of import order.
load_dotenv()

SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "devops-agent-sandbox:latest")
SANDBOX_TIMEOUT_SECONDS = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "60"))
SANDBOX_MEM_LIMIT = os.getenv("SANDBOX_MEM_LIMIT", "512m")
SANDBOX_CPU_LIMIT = float(os.getenv("SANDBOX_CPU_LIMIT", "1"))

GIT_AUTHOR_NAME = os.getenv("GIT_AUTHOR_NAME")
GIT_AUTHOR_EMAIL = os.getenv("GIT_AUTHOR_EMAIL")


class Sandbox:
    """
    Runs a shell command inside a short-lived, isolated Docker container
    instead of directly on the host machine.

    - Fresh container per call, removed immediately after — no state
      leaks between commands, no long-running container to babysit.
    - Runs on SANDBOX_IMAGE (default: devops-agent-sandbox:latest, built
      from Dockerfile.sandbox), which has git/curl preinstalled so common
      DevOps commands work without an install step. This matters because
      the sandbox is disposable per call — anything installed inside one
      container's filesystem is gone by the next call, so tools the
      agent needs regularly belong in the image, not installed at
      runtime.
    - The current working directory is mounted read-write at /workspace,
      so repo-relative commands (pytest, npm install, etc.) still work
      against real files.
    - Git commit identity (GIT_AUTHOR_NAME/EMAIL) is passed in as
      environment variables on every container, for the same reason as
      the image point above: `git config --global` run inside one
      container doesn't survive into the next one, so setting identity
      via git's own env-var mechanism is the only approach that actually
      persists across calls without needing a persistent volume.
    - Network is left enabled (see SANDBOX_ALLOW_NETWORK) since package
      installs and API/health checks are core to what this tool is for;
      isolation from the host is the safety boundary here, not isolation
      from the internet.
    - Memory, CPU, and wall-clock time are all capped so a runaway or
      malicious command can't consume the host or hang the agent.

    Only run_shell routes through this. git_* tools stay on direct
    subprocess calls — they're parameterized (git_push(remote, branch),
    not a raw string), so the injection surface that makes run_shell
    dangerous doesn't apply to them the same way.
    """

    def __init__(self):
        self._client: Optional["docker.DockerClient"] = None
        self._init_error: Optional[str] = None
        try:
            self._client = docker.from_env()
            self._client.ping()
        except DockerException as e:
            self._init_error = str(e)

    def run(self, command: str) -> ToolResult:
        if self._client is None:
            return ToolResult(
                success=False,
                output="",
                error=(
                    "Docker is not available "
                    f"({self._init_error}). Is Docker Desktop/daemon running?"
                ),
            )

        cwd = os.getcwd()
        container = None

        environment = {}
        if GIT_AUTHOR_NAME:
            environment["GIT_AUTHOR_NAME"] = GIT_AUTHOR_NAME
            environment["GIT_COMMITTER_NAME"] = GIT_AUTHOR_NAME
        if GIT_AUTHOR_EMAIL:
            environment["GIT_AUTHOR_EMAIL"] = GIT_AUTHOR_EMAIL
            environment["GIT_COMMITTER_EMAIL"] = GIT_AUTHOR_EMAIL

        try:
            container = self._client.containers.run(
                SANDBOX_IMAGE,
                command=["sh", "-c", command],
                volumes={cwd: {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                environment=environment,
                mem_limit=SANDBOX_MEM_LIMIT,
                nano_cpus=int(SANDBOX_CPU_LIMIT * 1_000_000_000),
                network_disabled=False,
                detach=True,
            )

            try:
                wait_result = container.wait(timeout=SANDBOX_TIMEOUT_SECONDS)
            except Exception:
                container.kill()
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Command timed out after {SANDBOX_TIMEOUT_SECONDS}s inside sandbox",
                )

            exit_code = wait_result.get("StatusCode", 1)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")

            if exit_code == 0:
                return ToolResult(success=True, output=logs)

            return ToolResult(
                success=False,
                output="",
                error=logs or f"Command exited with status {exit_code}",
            )

        except ImageNotFound:
            return ToolResult(
                success=False,
                output="",
                error=(
                    f"Sandbox image '{SANDBOX_IMAGE}' not found locally. "
                    "This is a custom image (not on a public registry) — "
                    "build it once with: "
                    "docker build -t devops-agent-sandbox:latest -f Dockerfile.sandbox ."
                ),
            )
        except DockerException as e:
            return ToolResult(success=False, output="", error=f"Sandbox error: {str(e)}")

        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass