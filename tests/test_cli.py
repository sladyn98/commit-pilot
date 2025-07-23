import unittest
from typer.testing import CliRunner

from cli import app

runner = CliRunner()


class TestCLI(unittest.TestCase):
    
    def test_help_command(self):
        """Test that the help command works without crashing"""
        result = runner.invoke(app, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("AI-powered git commit message generator", result.stdout)
    
    def test_dry_run_option_exists(self):
        """Test that --dry-run option is recognized"""
        result = runner.invoke(app, ["main", "--help"])
        self.assertIn("--dry-run", result.stdout)
    
    def test_unknown_option_fails(self):
        """Test that unknown options are rejected"""
        result = runner.invoke(app, ["--unknown-option"])
        self.assertEqual(result.exit_code, 2)  # Typer usage error
    
    def test_app_creation(self):
        """Test that the CLI app can be created without errors"""
        self.assertIsNotNone(app)
        self.assertEqual(app.info.name, "edgecommit")
        
    def test_basic_invocation_without_git_repo(self):
        """Test CLI behavior when not in git repo (should fail gracefully)"""
        # This will fail but should not crash the entire process  
        result = runner.invoke(app, ["main"])
        # Should exit with error code but not crash
        self.assertIn(result.exit_code, [1, 2])  # Either application error or usage error
        
    def test_dry_run_without_git_repo(self):
        """Test dry-run mode when not in git repo"""
        result = runner.invoke(app, ["main", "--dry-run"])
        # Should exit with error code but not crash
        self.assertIn(result.exit_code, [1, 2])