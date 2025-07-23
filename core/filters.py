import fnmatch
import re
from pathlib import Path
import tiktoken
from config import Config


class DiffFilter:
    
    def __init__(self, config: Config):
        self.config = config
    
    def should_skip_file(self, file_path: str) -> bool:
        path = Path(file_path)
        
        # read the commitpilotignore file
        try:
            with open(".commitpilotignore", "r") as commitpilotignore:
                lines = commitpilotignore.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Check if the pattern matches the file path
                        if fnmatch.fnmatch(str(path), line):
                            return True
        except FileNotFoundError:
            raise ValueError(".commitpilotignore file not found. ")
            pass

        return False
    
    def parse_diff_patch_file(self, patch_file: str) -> str:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(patch_file)
        MAX = 6000           # pick a ceiling that leaves headroom for the prompt

        if len(tokens) > MAX:
            truncated_diff = enc.decode(tokens[:MAX])
            truncated_diff += "\n# …truncated by CommitPilot ({} tokens)\n".format(len(tokens) - MAX)
            return truncated_diff

        return patch_file
    
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
        result = []
        file_line_count = 0
        in_file_diff = False
        
        for line in lines:
            if line.startswith('diff --git'):
                file_line_count = 0
                in_file_diff = True
            
            if in_file_diff and file_line_count >= max_lines:
                if not line.startswith('diff --git'):
                    continue
            
            result.append(line)
            if in_file_diff:
                file_line_count += 1
        
        return '\n'.join(result)