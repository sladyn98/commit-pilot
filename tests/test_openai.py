import os
from unittest.mock import Mock, patch

import pytest

from edgecommit.config import Config
from edgecommit.core.analyzer import DiffStats, DiffSummary, FileDiff
from edgecommit.llm.openai import OpenAIProvider


class TestOpenAIProvider:
    @pytest.fixture
    def config(self):
        return Config(
            openai_api_key="test-key",
            openai_model="gpt-4",
            openai_temperature=0.7,
            openai_max_tokens=500,
            request_timeout=30,
            max_retries=3,
        )
    
    @pytest.fixture
    def diff_summary(self):
        return DiffSummary(
            stats=DiffStats(files_changed=2, insertions=10, deletions=5),
            files=[
                FileDiff(
                    path="src/main.py",
                    additions=8,
                    deletions=3,
                    is_new=False,
                    is_deleted=False,
                    is_renamed=False,
                ),
                FileDiff(
                    path="tests/test_main.py",
                    additions=2,
                    deletions=2,
                    is_new=False,
                    is_deleted=False,
                    is_renamed=False,
                ),
            ],
            change_type="feat",
            primary_changes=["Extended src/main.py", "Modified tests/test_main.py"],
        )
    
    def test_init_with_api_key(self, config):
        provider = OpenAIProvider(config)
        assert provider.api_key == "test-key"
    
    def test_init_without_api_key(self):
        config = Config()
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                OpenAIProvider(config)
    
    def test_init_with_env_api_key(self):
        config = Config()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAIProvider(config)
            assert provider.api_key == "env-key"
    
    @patch("edgecommit.llm.openai.OpenAI")
    def test_client_lazy_initialization(self, mock_openai_class, config):
        provider = OpenAIProvider(config)
        
        
        mock_openai_class.assert_not_called()
        
        
        client = provider.client
        
        
        mock_openai_class.assert_called_once_with(
            api_key="test-key",
            timeout=30,
            max_retries=3,
        )
        
        
        client2 = provider.client
        assert client is client2
        assert mock_openai_class.call_count == 1
    
    @patch("edgecommit.llm.openai.OpenAI")
    def test_generate_commit_success(self, mock_openai_class, config, diff_summary):
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="feat: add new feature\n\nImplemented user authentication"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(config)
        result = provider.generate_commit(diff_summary)
        
        assert result == "feat: add new feature\n\nImplemented user authentication"
        
        
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 500
    
    @patch("edgecommit.llm.openai.OpenAI")
    def test_generate_commit_truncates_long_subject(self, mock_openai_class, config, diff_summary):
        
        mock_client = Mock()
        mock_response = Mock()
        long_subject = "feat: " + "x" * 100  
        mock_response.choices = [Mock(message=Mock(content=long_subject))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(config)
        result = provider.generate_commit(diff_summary)
        
        
        assert len(result.split("\n")[0]) == 72
        assert result.endswith("...")
    
    @patch("edgecommit.llm.openai.OpenAI")
    def test_generate_commit_empty_response(self, mock_openai_class, config, diff_summary):
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(config)
        
        with pytest.raises(RuntimeError, match="Failed to generate commit message"):
            provider.generate_commit(diff_summary)
    
    @patch("edgecommit.llm.openai.OpenAI")
    def test_generate_commit_api_error(self, mock_openai_class, config, diff_summary):
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(config)
        
        with pytest.raises(RuntimeError, match="Failed to generate commit message: API Error"):
            provider.generate_commit(diff_summary)
    
    def test_import_error_handling(self, config):
        
        with patch.dict("sys.modules", {"openai": None}):
            provider = OpenAIProvider(config)
            with pytest.raises(ImportError, match="OpenAI package not installed"):
                _ = provider.client