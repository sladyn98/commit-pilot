from unittest.mock import Mock, patch

import unittest
from typer.testing import CliRunner

from edgecommit.cli import app
from edgecommit.core.analyzer import DiffStats, DiffSummary, FileDiff
from edgecommit.core.git import GitError

runner = CliRunner()


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.mock_diff_summary = DiffSummary(
            stats=DiffStats(files_changed=1, insertions=5, deletions=2),
            files=[
                FileDiff(
                    path="src/feature.py",
                    additions=5,
                    deletions=2,
                    is_new=False,
                    is_deleted=False,
                    is_renamed=False,
                )
            ],
            change_type="feat",
            primary_changes=["Extended src/feature.py"],
        )
    
    @patch("edgecommit.cli.git.has_staged_changes")
    def test_no_staged_changes(self, mock_has_staged):
        mock_has_staged.return_value = False
        
        result = runner.invoke(app, [])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No staged changes found", result.stdout)
    
    @patch("edgecommit.cli.Config")
    @patch("edgecommit.cli.get_provider")
    @patch("edgecommit.cli.analyzer.analyze_diff")
    @patch("edgecommit.cli.git.create_commit")
    @patch("edgecommit.cli.git.get_staged_diff")
    @patch("edgecommit.cli.git.has_staged_changes")
    @patch("edgecommit.cli.typer.confirm")
    def test_successful_commit(
        self,
        mock_confirm,
        mock_has_staged,
        mock_get_diff,
        mock_create_commit,
        mock_analyze,
        mock_get_provider,
        mock_config,
        self.mock_diff_summary,
    ):
        
        mock_has_staged.return_value = True
        mock_get_diff.return_value = "diff content"
        mock_analyze.return_value = self.mock_diff_summary
        mock_provider = Mock()
        mock_provider.generate_commit.return_value = "feat: add new feature\n\nImplemented feature X"
        mock_get_provider.return_value = mock_provider
        mock_confirm.return_value = True
        
        result = runner.invoke(app, [])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Generated commit message:", result.stdout)
        self.assertIn("feat: add new feature", result.stdout)
        self.assertIn("Commit created successfully!", result.stdout)
        
        mock_create_commit.assert_called_once_with("feat: add new feature\n\nImplemented feature X")
    
    @patch("edgecommit.cli.Config")
    @patch("edgecommit.cli.get_provider")
    @patch("edgecommit.cli.analyzer.analyze_diff")
    @patch("edgecommit.cli.git.get_staged_diff")
    @patch("edgecommit.cli.git.has_staged_changes")
    def test_dry_run_mode(
        self,
        mock_has_staged,
        mock_get_diff,
        mock_analyze,
        mock_get_provider,
        mock_config,
        self.mock_diff_summary,
    ):
        
        mock_has_staged.return_value = True
        mock_get_diff.return_value = "diff content"
        mock_analyze.return_value = self.mock_diff_summary
        mock_provider = Mock()
        mock_provider.generate_commit.return_value = "feat: test message"
        mock_get_provider.return_value = mock_provider
        
        result = runner.invoke(app, ["--dry-run"])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Generated commit message:", result.stdout)
        self.assertIn("feat: test message", result.stdout)
        self.assertIn("Dry run mode - no commit created", result.stdout)
    
    @patch("edgecommit.cli.git.has_staged_changes")
    @patch("edgecommit.cli.git.get_staged_diff")
    def test_git_error_handling(self, mock_get_diff, mock_has_staged):
        mock_has_staged.return_value = True
        mock_get_diff.side_effect = GitError("Not a git repository")
        
        result = runner.invoke(app, [])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Git error: Not a git repository", result.stdout)
    
    @patch("edgecommit.cli.Config")
    @patch("edgecommit.cli.get_provider")
    def test_configuration_error(self, mock_get_provider, mock_config):
        mock_config.side_effect = ValueError("Missing API key")
        
        result = runner.invoke(app, [])
        
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Configuration error", result.stdout)
    
    @patch("edgecommit.cli.Config")
    @patch("edgecommit.cli.get_provider")
    @patch("edgecommit.cli.analyzer.analyze_diff")
    @patch("edgecommit.cli.git.create_commit")
    @patch("edgecommit.cli.git.get_staged_diff")
    @patch("edgecommit.cli.git.has_staged_changes")
    @patch("edgecommit.cli.typer.confirm")
    def test_user_cancels_commit(
        self,
        mock_confirm,
        mock_has_staged,
        mock_get_diff,
        mock_create_commit,
        mock_analyze,
        mock_get_provider,
        mock_config,
        self.mock_diff_summary,
    ):
        
        mock_has_staged.return_value = True
        mock_get_diff.return_value = "diff content"
        mock_analyze.return_value = self.mock_diff_summary
        mock_provider = Mock()
        mock_provider.generate_commit.return_value = "feat: test"
        mock_get_provider.return_value = mock_provider
        mock_confirm.return_value = False  
        
        result = runner.invoke(app, [])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Commit cancelled", result.stdout)
        mock_create_commit.assert_not_called()
    
    def test_custom_provider_option(self):
        with patch("edgecommit.cli.git.has_staged_changes") as mock_has_staged:
            mock_has_staged.return_value = False
            
            result = runner.invoke(app, ["--provider", "custom"])
            
            
            self.assertEqual(result.exit_code, 1)
            self.assertIn("No staged changes found", result.stdout)