import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class GitError(Exception):
    pass


@dataclass
class NumStat:
    added: int
    removed: int
    file_path: str
    is_binary: bool = False
    is_renamed: bool = False
    old_path: Optional[str] = None


def _run_git_command(args: list[str], cwd: Optional[Path] = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git command failed: {e.stderr.strip()}") from e


def has_staged_changes(cwd: Optional[Path] = None) -> bool:
    try:
        _run_git_command(["diff", "--cached", "--quiet"], cwd)
        return False
    except GitError:
        return True


def get_staged_diff(cwd: Optional[Path] = None) -> str:
    diff = _run_git_command(["diff", "--cached", "-w"], cwd)
    if not diff:
        raise GitError("No staged changes found")
    return diff

def get_diff_patch(cwd: Optional[Path] = None) -> str:
    print("Running diff patch")
    diff = _run_git_command(["diff", "--cached", "--unified=0", "--no-color"], cwd)
    if not diff:
        raise GitError("No staged changes found")
    return diff


def get_staged_numstat(cwd: Optional[Path] = None) -> list[NumStat]:
    try:
        output = _run_git_command(["diff", "--cached", "--numstat"], cwd)
        if not output:
            return []
        
        stats = []
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) < 3:
                continue
            
            added_str, removed_str = parts[0], parts[1]
            file_path = parts[2]
            
            
            if added_str == '-' and removed_str == '-':
                stats.append(NumStat(
                    added=0,
                    removed=0,
                    file_path=file_path,
                    is_binary=True
                ))
                continue
            
            
            old_path = None
            is_renamed = False
            if ' => ' in file_path:
                old_path, file_path = file_path.split(' => ', 1)
                
                if file_path.startswith('{') and file_path.endswith('}'):
                    file_path = file_path[1:-1]
                if old_path.startswith('{') and old_path.endswith('}'):
                    old_path = old_path[1:-1]
                is_renamed = True
            
            try:
                added = int(added_str)
                removed = int(removed_str)
            except ValueError:
                
                added = removed = 0
            
            stats.append(NumStat(
                added=added,
                removed=removed,
                file_path=file_path,
                is_binary=False,
                is_renamed=is_renamed,
                old_path=old_path
            ))
        
        return stats
    except GitError:
        return []


def create_commit(message: str, cwd: Optional[Path] = None) -> None:
    if not message:
        raise ValueError("Commit message cannot be empty")
    
    if not has_staged_changes(cwd):
        raise GitError("No staged changes to commit")
    
    _run_git_command(["commit", "-m", message], cwd)


def get_editor_fallback_template() -> str:
    return """# Auto-commit fallback - please edit this commit message
# 
# Staged changes detected but could not generate AI commit message.
# Please write a conventional commit message:
#
# Format: <type>(<scope>): <subject>
#
# Types: feat, fix, docs, style, refactor, perf, test, chore
# 
# Example:
# feat(auth): add user login validation
# 
# Body can be added below (optional):

"""