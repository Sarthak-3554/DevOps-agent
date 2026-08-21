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


if __name__ == "__main__":
    unittest.main()