import pytest

from edgecommit.core.redaction import SecretRedactor


class TestSecretRedactor:
    @pytest.fixture
    def redactor(self):
        return SecretRedactor()
    
    def test_redacts_openai_api_keys(self, redactor):
        line = '+    api_key = "sk-1234567890abcdef1234567890abcdef12345678"'
        redacted = redactor.redact_line(line)
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in redacted
        assert "sk-1...5678" in redacted
    
    def test_redacts_github_tokens(self, redactor):
        line = '+    token = "ghp_1234567890abcdef1234567890abcdef12"'
        redacted = redactor.redact_line(line)
        assert "ghp_1234567890abcdef1234567890abcdef12" not in redacted
        assert "ghp_...ef12" in redacted
    
    def test_redacts_long_strings_with_keywords(self, redactor):
        line = '+    password = "this_is_a_very_long_password_that_should_be_redacted_because_it_contains_sensitive_information"'
        redacted = redactor.redact_line(line)
        assert "this_is_a_very_long_password_that_should_be_redacted_because_it_contains_sensitive_information" not in redacted
        assert "this...tion" in redacted
    
    def test_does_not_redact_short_strings(self, redactor):
        line = '+    name = "John"'
        redacted = redactor.redact_line(line)
        assert redacted == line
    
    def test_does_not_redact_normal_variables(self, redactor):
        line = '+    config_file = "this_is_a_normal_config_file_path_that_should_not_be_redacted"'
        redacted = redactor.redact_line(line)
        assert redacted == line
    
    def test_redacts_aws_keys(self, redactor):
        line = '+    aws_key = "AKIAIOSFODNN7EXAMPLE"'
        redacted = redactor.redact_line(line)
        assert "AKIAIOSFODNN7EXAMPLE" not in redacted
        assert "AKIA...MPLE" in redacted
    
    def test_redacts_multiple_secrets_in_line(self, redactor):
        line = '+    config = {"api_key": "sk-1234567890abcdef1234567890abcdef12345678", "token": "ghp_1234567890abcdef1234567890abcdef12"}'
        redacted = redactor.redact_line(line)
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in redacted
        assert "ghp_1234567890abcdef1234567890abcdef12" not in redacted
        assert "sk-1...5678" in redacted
        assert "ghp_...ef12" in redacted
    
    def test_redact_diff_only_processes_added_lines(self, redactor):
        diff = """-    old_secret = "sk-1234567890abcdef1234567890abcdef12345678"
+    new_secret = "sk-abcdef1234567890abcdef1234567890abcdef12"
     normal_line = "not changed"
+    another_line = "regular content"
        
        diff_without_secrets = """+    name = "John"
+    version = "1.0.0"
        
        redacted = redactor.redact_diff(diff)
        
        
        assert "diff --git a/config.py b/config.py" in redacted
        assert "index 1234567..abcdefg 100644" in redacted
        assert "--- a/config.py" in redacted
        assert "+++ b/config.py" in redacted
        assert "@@ -1,3 +1,4 @@" in redacted
        
        
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in redacted
        assert "sk-1...5678" in redacted