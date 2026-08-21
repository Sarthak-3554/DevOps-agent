import unittest

from agent.safety import SafetyLayer


class SafetyLayerTests(unittest.TestCase):
    def test_shell_blacklist_flags_process_killers(self):
        self.assertTrue(SafetyLayer.is_shell_dangerous("pkill -9 -u $USER"))
        self.assertTrue(SafetyLayer.is_shell_dangerous("killall python"))
        self.assertTrue(SafetyLayer.is_shell_dangerous("kill -9 1234"))

    def test_shell_blacklist_allows_read_only_commands(self):
        self.assertFalse(SafetyLayer.is_shell_dangerous("ls -la"))
        self.assertFalse(SafetyLayer.is_shell_dangerous("git status"))


if __name__ == "__main__":
    unittest.main()
