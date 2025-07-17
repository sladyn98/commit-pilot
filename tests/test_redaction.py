import unittest

from edgecommit.core.redaction import SecretRedactor


class TestSecretRedactor(unittest.TestCase):
    def setUp(self):
        self.redactor = SecretRedactor()
    
    def test_redacts_openai_api_keys(self):
        line = '+    api_key = "sk-1234567890abcdef1234567890abcdef12345678"'
        redacted = self.redactor.redact_line(line)
        self.assertNotIn("sk-1234567890abcdef1234567890abcdef12345678", redacted)
        self.assertIn("sk-1...5678", redacted)
    
    def test_redacts_github_tokens(self):
        line = '+    token = "ghp_1234567890abcdef1234567890abcdef12"'
        redacted = self.redactor.redact_line(line)
        self.assertNotIn("ghp_1234567890abcdef1234567890abcdef12", redacted)
        self.assertIn("ghp_...ef12", redacted)
    
    def test_does_not_redact_short_strings(self):
        line = '+    name = "John"'
        redacted = self.redactor.redact_line(line)
        self.assertEqual(redacted, line)
    
    def test_redact_diff_only_processes_added_lines(self):
        diff = """-    old_secret = "sk-1234567890abcdef1234567890abcdef12345678"
+    new_secret = "sk-abcdef1234567890abcdef1234567890abcdef12"
     normal_line = "not changed"
+    another_line = "regular content"
"""
        redacted = self.redactor.redact_diff(diff)
        
        # Old secret should not be redacted (it's a deletion)
        self.assertIn("sk-1234567890abcdef1234567890abcdef12345678", redacted)
        
        # New secret should be redacted (it's an addition)
        self.assertNotIn("sk-abcdef1234567890abcdef1234567890abcdef12", redacted)
        self.assertIn("sk-a...ef12", redacted)
    
    def test_has_potential_secrets_detection(self):
        diff_with_secrets = """+    api_key = "sk-1234567890abcdef1234567890abcdef12345678"
+    password = "very_long_password_that_looks_suspicious"
"""
        
        diff_without_secrets = """+    name = "John"
+    version = "1.0.0"
"""
        
        self.assertTrue(self.redactor.has_potential_secrets(diff_with_secrets))
        self.assertFalse(self.redactor.has_potential_secrets(diff_without_secrets))