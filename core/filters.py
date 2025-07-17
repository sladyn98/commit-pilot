import fnmatch
import re
from pathlib import Path

from edgecommit.config import Config


class DiffFilter:
    
    def __init__(self, config: Config):
        self.config = config
        
        
        self.ignore_patterns = [
            
            "*.lock", "package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock",
            
            "*.pyc", "*.pyo", "*.class", "*.o", "*.so", "*.dll", "*.exe",
            "*.min.js", "*.min.css", "*.map",
            
            "dist/", "build/", "target/", "out/", ".next/", ".nuxt/",
            
            "node_modules/", "vendor/", ".venv/", "venv/", "__pycache__/",
            
            ".vscode/", ".idea/", ".DS_Store", "Thumbs.db", "*.swp", "*.swo",
            
            "*.log", "*.tmp", "*.temp", "logs/", "tmp/",
        ]
        
        
        self.ignore_patterns.extend(config.extra_ignore_patterns)
        
        
        self.binary_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
            ".woff", ".woff2", ".ttf", ".otf", ".eot",
            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
            ".zip", ".tar", ".gz", ".rar", ".7z",
            ".mp3", ".mp4", ".avi", ".mkv", ".mov",
        }
    
    def should_skip_file(self, file_path: str) -> bool:
        path = Path(file_path)
        
        
        if path.suffix.lower() in self.binary_extensions:
            return True
        
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
        
        return False
    
    def filter_diff(self, raw_diff: str) -> str:
        if not raw_diff:
            return raw_diff
        
        lines = raw_diff.split('\n')
        filtered_lines = []
        current_file = None
        skip_current_file = False
        
        for line in lines:
            if line.startswith('diff --git'):
                
                match = re.match(r'diff --git a/(.*) b/(.*)', line)
                if match:
                    current_file = match.group(2)  
                    skip_current_file = self.should_skip_file(current_file)
                else:
                    skip_current_file = False
            
            if not skip_current_file:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def clamp_large_file_diff(self, diff_content: str, max_lines: int = 200) -> str:
        lines = diff_content.split('\n')
        if len(lines) <= max_lines:
            return diff_content
        
        
        header_lines = []
        content_lines = []
        
        for line in lines:
            if (line.startswith('diff --git') or 
                line.startswith('index ') or 
                line.startswith('---') or 
                line.startswith('+++')):
                header_lines.append(line)
            else:
                content_lines.append(line)
        
        if len(content_lines) > max_lines:
            
            keep_lines = max_lines // 4
            clamped_content = (
                content_lines[:keep_lines] + 
                [f'... <{len(content_lines) - 2 * keep_lines} lines omitted> ...'] +
                content_lines[-keep_lines:]
            )
            return '\n'.join(header_lines + clamped_content)
        
        return diff_content