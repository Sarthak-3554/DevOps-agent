import json
import os
import shutil
import tempfile
import unittest

from agent.logger import AuditLogger, new_session_id


class AuditLoggerTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "nested", "audit.jsonl")
        self.logger = AuditLogger(path=self.path)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _read_lines(self):
        with open(self.path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_creates_parent_directories(self):
        self.assertTrue(os.path.isdir(os.path.dirname(self.path)))

    def test_log_tool_call_writes_valid_json_line(self):
        self.logger.log_tool_call(
            session_id="abc123",
            tool="git_push",
            arguments={"branch": "main"},
            sandboxed=False,
            required_confirmation=True,
            confirmed=True,
            success=True,
            error=None,
            duration_ms=123.4,
        )

        lines = self._read_lines()
        self.assertEqual(len(lines), 1)
        record = lines[0]
        self.assertEqual(record["event"], "tool_call")
        self.assertEqual(record["tool"], "git_push")
        self.assertEqual(record["session_id"], "abc123")
        self.assertTrue(record["success"])
        self.assertIn("timestamp", record)

    def test_log_llm_call_writes_valid_json_line(self):
        self.logger.log_llm_call(
            session_id="abc123",
            iteration=1,
            model="groq/openai/gpt-oss-120b",
            tool_call_count=1,
            has_final_answer=False,
            duration_ms=500.0,
        )

        lines = self._read_lines()
        self.assertEqual(lines[0]["event"], "llm_call")
        self.assertEqual(lines[0]["model"], "groq/openai/gpt-oss-120b")

    def test_multiple_calls_append_as_separate_lines(self):
        self.logger.log_tool_call(
            session_id="s1", tool="git_status", arguments={},
            sandboxed=False, required_confirmation=False, confirmed=None,
            success=True, error=None, duration_ms=10.0,
        )
        self.logger.log_tool_call(
            session_id="s1", tool="run_shell", arguments={"command": "ls"},
            sandboxed=True, required_confirmation=False, confirmed=None,
            success=True, error=None, duration_ms=200.0,
        )

        lines = self._read_lines()
        self.assertEqual(len(lines), 2)

    def test_session_ids_are_unique(self):
        ids = {new_session_id() for _ in range(200)}
        self.assertEqual(len(ids), 200)


if __name__ == "__main__":
    unittest.main()