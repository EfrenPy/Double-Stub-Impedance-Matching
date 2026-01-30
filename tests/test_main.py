"""Tests for __main__.py module entry point."""

import subprocess
import sys


class TestMainModule:
    def test_module_runs(self):
        result = subprocess.run(
            [sys.executable, '-m', 'double_stub'],
            capture_output=True, text=True,
            cwd=None,
        )
        assert result.returncode == 0
        assert 'Double-Stub' in result.stdout
