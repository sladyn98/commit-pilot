import re
from typing import Set


class SecretRedactor:
    
    def __init__(self):
        
        self.secret_keywords = {
            'password', 'secret', 'token', 'key', 'api_key', 'apikey',
            'auth', 'credential', 'private', 'priv', 'access_key',
            'session', 'cookie', 'jwt', 'bearer', 'oauth',
        }
        
        
        self.secret_patterns = [
            
            r'["\']([a-zA-Z0-9+/=]{40,})["\']',  
            r'["\']([a-fA-F0-9]{32,})["\']',     
            r'["\']([a-zA-Z0-9_-]{50,})["\']',   
            
            
            r'["\']sk-[a-zA-Z0-9]{48}["\']',     
            r'["\']ghp_[a-zA-Z0-9]{36}["\']',    
            r'["\']ghs_[a-zA-Z0-9]{36}["\']',    
            r'["\']AKIA[0-9A-Z]{16}["\']',       
            r'["\']ya29\.[a-zA-Z0-9_-]{100,}["\']', 
        ]
        
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.secret_patterns]
    
    def _looks_like_secret(self, value: str) -> bool:
        if len(value) < 40:
            return False
        
        
        
        return any(keyword in value.lower() for keyword in self.secret_keywords)
    
    def _redact_string(self, value: str) -> str:
        if len(value) <= 8:
            return value
        
        
        return f"{value[:4]}...{value[-4:]}"
    
    def redact_line(self, line: str) -> str:
        redacted_line = line
        
        
        for pattern in self.compiled_patterns:
            def replace_match(match):
                secret = match.group(1)
                redacted = self._redact_string(secret)
                return match.group(0).replace(secret, redacted)
            
            redacted_line = pattern.sub(replace_match, redacted_line)
        
        
        quote_pattern = r'(["\'])([^"\']{40,})\1'
        def replace_long_string(match):
            quote = match.group(1)
            content = match.group(2)
            
            
            if self._looks_like_secret(content):
                redacted = self._redact_string(content)
                return f"{quote}{redacted}{quote}"
            return match.group(0)
        
        redacted_line = re.sub(quote_pattern, replace_long_string, redacted_line)
        
        return redacted_line
    
    def redact_diff(self, diff_content: str) -> str:
        lines = diff_content.split('\n')
        redacted_lines = []
        
        for line in lines:
            
            if line.startswith('+') and not line.startswith('+++'):
                redacted_lines.append(self.redact_line(line))
            else:
                redacted_lines.append(line)
        
        return '\n'.join(redacted_lines)
    
    def has_potential_secrets(self, diff_content: str) -> bool:
        
        for pattern in self.compiled_patterns:
            if pattern.search(diff_content):
                return True
        
        
        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in self.secret_keywords):
                    
                    if re.search(r'["\'][^"\']{30,}["\']', line):
                        return True
        
        return False