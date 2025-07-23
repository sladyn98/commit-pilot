import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import unittest

from core.git import GitError, create_commit, get_staged_diff, has_staged_changes


class TestGitFunctions(unittest.TestCase):
    @patch("subprocess.run")
    def test_has_staged_changes_true(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["git"], stderr="")
        self.assertTrue(has_staged_changes())
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
            text=True,
            check=True,
            cwd=None,
        )

    @patch("subprocess.run")
    def test_has_staged_changes_false(self, mock_run):
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
        self.assertFalse(has_staged_changes())

    @patch("subprocess.run")
    def test_get_staged_diff_success(self, mock_run):
        expected_diff = "diff --git a/file.txt b/file.txt\n+added line"
        mock_run.return_value = Mock(stdout=expected_diff, stderr="", returncode=0)
        
        result = get_staged_diff()
        self.assertEqual(result, expected_diff.strip())
        mock_run.assert_called_once_with(
            ["git", "diff", "--cached", "-w"],
            capture_output=True,
            text=True,
            check=True,
            cwd=None,
        )

    @patch("subprocess.run")
    def test_get_staged_diff_no_changes(self, mock_run):
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
        
        with self.assertRaises(GitError):
            get_staged_diff()

    @patch("subprocess.run")
    def test_get_staged_diff_git_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["git"], stderr="fatal: not a git repository"
        )
        
        with self.assertRaises(GitError):
            get_staged_diff()

    @patch("core.git.has_staged_changes")
    @patch("subprocess.run")
    def test_create_commit_success(self, mock_run, mock_has_staged):
        mock_has_staged.return_value = True
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
        
        create_commit("feat: add new feature")
        mock_run.assert_called_once_with(
            ["git", "commit", "-m", "feat: add new feature"],
            capture_output=True,
            text=True,
            check=True,
            cwd=None,
        )

    def test_create_commit_empty_message(self):
        with self.assertRaises(ValueError):
            create_commit("")

    @patch("core.git.has_staged_changes")
    def test_create_commit_no_staged_changes(self, mock_has_staged):
        mock_has_staged.return_value = False
        
        with self.assertRaises(GitError):
            create_commit("feat: test")

    @patch("subprocess.run")
    def test_git_command_with_cwd(self, mock_run):
        mock_run.return_value = Mock(stdout="output", stderr="", returncode=0)
        test_path = Path("/test/path")
        
        has_staged_changes(cwd=test_path)
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args[1]["cwd"], test_path)