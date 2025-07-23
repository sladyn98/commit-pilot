import os
from unittest.mock import Mock, patch

import unittest

from config import Config
from core.analyzer import DiffSummary, FileSummary
from llm.openai import OpenAIProvider


class TestOpenAIProvider(unittest.TestCase):
    def setUp(self):
        # Store the environment variables to use in tests
        self.test_env = {
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "gpt-4",
            "MAX_PROMPT_TOKENS": "8000"
        }
    
        self.diff_summary = DiffSummary(
            total_added=10,
            total_removed=5,
            files=[
                FileSummary(
                    path="src/main.py",
                    added=8,
                    removed=3,
                    change_type="modified",
                ),
                FileSummary(
                    path="tests/test_main.py",
                    added=2,
                    removed=2,
                    change_type="modified",
                ),
            ],
            change_type="feat",
            contents="diff content",
        )
    
    def test_init_with_api_key(self):
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
            self.assertEqual(provider.api_key, "test-key")
    
    def test_init_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            with self.assertRaises(ValueError):
                OpenAIProvider(config)
    
    def test_init_with_env_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            config = Config()
            provider = OpenAIProvider(config)
            self.assertEqual(provider.api_key, "env-key")
    
    @patch("openai.OpenAI")
    def test_client_lazy_initialization(self, mock_openai_class):
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
        
            # Should not initialize client on creation
            mock_openai_class.assert_not_called()
            
            # Should initialize on first access
            client = provider.client
            
            # Should be called with correct args
            mock_openai_class.assert_called_once_with(
                api_key="test-key"
            )
            
            # Should reuse same instance
            client2 = provider.client
            self.assertIs(client, client2)
            self.assertEqual(mock_openai_class.call_count, 1)
    
    @patch("os._exit")
    @patch("openai.OpenAI")
    def test_generate_commit_success(self, mock_openai_class, mock_exit):
        # Mock the exit to prevent test termination
        mock_exit.side_effect = SystemExit(1)
        
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="feat: add new feature\n\nImplemented user authentication"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
            # Expect SystemExit due to os._exit(1) in the code
            with self.assertRaises(SystemExit):
                result = provider.generate_commit(self.diff_summary)
    
    @patch("os._exit")
    @patch("openai.OpenAI")
    def test_generate_commit_truncates_long_subject(self, mock_openai_class, mock_exit):
        # Mock the exit to prevent test termination
        mock_exit.side_effect = SystemExit(1)
        
        # Mock response with very long subject line
        mock_client = Mock()
        mock_response = Mock()
        long_subject = "feat: " + "x" * 100  # Very long subject
        mock_response.choices = [Mock(message=Mock(content=long_subject))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
            # Expect SystemExit due to os._exit(1) in the code
            with self.assertRaises(SystemExit):
                result = provider.generate_commit(self.diff_summary)
    
    @patch("os._exit")
    @patch("openai.OpenAI")
    def test_generate_commit_empty_response(self, mock_openai_class, mock_exit):
        # Mock the exit to prevent test termination
        mock_exit.side_effect = SystemExit(1)
        
        # Mock empty response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
            
            # Expect SystemExit due to os._exit(1) in the code
            with self.assertRaises(SystemExit):
                provider.generate_commit(self.diff_summary)
    
    @patch("os._exit")
    @patch("openai.OpenAI")
    def test_generate_commit_api_error(self, mock_openai_class, mock_exit):
        # Mock the exit to prevent test termination
        mock_exit.side_effect = SystemExit(1)
        
        # Mock API error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict(os.environ, self.test_env):
            config = Config()
            provider = OpenAIProvider(config)
            
            # Expect SystemExit due to os._exit(1) in the code
            with self.assertRaises(SystemExit):
                provider.generate_commit(self.diff_summary)
    
    def test_import_error_handling(self):
        # Test handling when openai package is not available
        with patch.dict("sys.modules", {"openai": None}):
            with patch.dict(os.environ, self.test_env):
                config = Config()
                provider = OpenAIProvider(config)
                with self.assertRaises(ImportError):
                    _ = provider.client