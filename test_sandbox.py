import unittest
from unittest.mock import MagicMock, patch

from docker.errors import DockerException, ImageNotFound

from tools.sandbox import Sandbox


class SandboxTests(unittest.TestCase):
    @patch("tools.sandbox.docker.from_env")
    def test_docker_unavailable_returns_clean_failure(self, mock_from_env):
        mock_from_env.side_effect = DockerException("cannot connect to docker daemon")

        sandbox = Sandbox()
        result = sandbox.run("ls")

        self.assertFalse(result.success)
        self.assertIn("Docker is not available", result.error)

    @patch("tools.sandbox.docker.from_env")
    def test_successful_command_returns_output(self, mock_from_env):
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"hello from sandbox\n"
        mock_client.containers.run.return_value = mock_container

        sandbox = Sandbox()
        result = sandbox.run("echo hello from sandbox")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "hello from sandbox\n")
        mock_container.remove.assert_called_once_with(force=True)

    @patch("tools.sandbox.docker.from_env")
    def test_nonzero_exit_returns_failure_with_logs(self, mock_from_env):
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.return_value = b"command not found: fakecmd\n"
        mock_client.containers.run.return_value = mock_container

        sandbox = Sandbox()
        result = sandbox.run("fakecmd")

        self.assertFalse(result.success)
        self.assertIn("command not found", result.error)
        mock_container.remove.assert_called_once_with(force=True)

    @patch("tools.sandbox.docker.from_env")
    def test_timeout_kills_and_removes_container(self, mock_from_env):
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("timed out")
        mock_client.containers.run.return_value = mock_container

        sandbox = Sandbox()
        result = sandbox.run("sleep 999")

        self.assertFalse(result.success)
        self.assertIn("timed out", result.error.lower())
        mock_container.kill.assert_called_once()
        mock_container.remove.assert_called_once_with(force=True)

    @patch("tools.sandbox.docker.from_env")
    def test_missing_image_gives_actionable_error(self, mock_from_env):
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = ImageNotFound("no such image")

        sandbox = Sandbox()
        result = sandbox.run("ls")

        self.assertFalse(result.success)
        self.assertIn("docker build", result.error)

    @patch("tools.sandbox.docker.from_env")
    def test_container_always_removed_even_on_docker_exception(self, mock_from_env):
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.wait.side_effect = DockerException("boom")
        mock_client.containers.run.return_value = mock_container

        sandbox = Sandbox()
        result = sandbox.run("ls")

        self.assertFalse(result.success)
        mock_container.remove.assert_called_once_with(force=True)

    @patch.dict("os.environ", {"GIT_AUTHOR_NAME": "Sarthak", "GIT_AUTHOR_EMAIL": "sarthak@example.com"})
    @patch("tools.sandbox.docker.from_env")
    def test_git_identity_env_vars_are_passed_to_every_container(self, mock_from_env):
        # Regression test for the real issue: `git config --global` run
        # inside one container doesn't survive into the next disposable
        # container, so every git commit kept failing with "Author
        # identity unknown". The fix is passing identity as env vars on
        # each container run instead of relying on a config file persisting.
        import importlib

        import tools.sandbox as sandbox_module
        importlib.reload(sandbox_module)  # picks up the patched env vars

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b"[main abc1234] Readme updated\n"
        mock_client.containers.run.return_value = mock_container

        sandbox = sandbox_module.Sandbox()
        sandbox.run('git commit -m "Readme updated"')

        _, call_kwargs = mock_client.containers.run.call_args
        env = call_kwargs.get("environment", {})
        self.assertEqual(env.get("GIT_AUTHOR_NAME"), "Sarthak")
        self.assertEqual(env.get("GIT_COMMITTER_NAME"), "Sarthak")
        self.assertEqual(env.get("GIT_AUTHOR_EMAIL"), "sarthak@example.com")
        self.assertEqual(env.get("GIT_COMMITTER_EMAIL"), "sarthak@example.com")

        importlib.reload(sandbox_module)  # restore for other tests
        
if __name__ == "__main__":
    unittest.main()