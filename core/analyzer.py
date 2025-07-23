from dataclasses import dataclass
from typing import Literal

from core.git import NumStat

ChangeType = Literal["feat", "fix", "refactor", "style", "docs", "test", "chore", "perf"]


@dataclass
class FileSummary:
    path: str
    added: int
    removed: int
    change_type: Literal["added", "deleted", "modified", "renamed"]
    old_path: str | None = None


@dataclass
class DiffSummary:
    files: list[FileSummary]
    total_added: int
    total_removed: int
    change_type: ChangeType
    contents: str
    
    @property
    def total_files(self) -> int:
        return len(self.files)
    
    @property
    def significant_files(self) -> list[FileSummary]:
        return [f for f in self.files if (f.added + f.removed) > 5]


def _determine_change_type(files: list[FileSummary]) -> ChangeType:
    """Determine the overall change type based on the files modified."""
    # Simple heuristic - can be improved
    paths = [f.path.lower() for f in files]
    
    if any("test" in p for p in paths):
        return "test"
    elif any("docs" in p or "readme" in p or ".md" in p for p in paths):
        return "docs"
    elif any(".css" in p or ".scss" in p or "style" in p for p in paths):
        return "style"
    elif any("perf" in p or "optim" in p for p in paths):
        return "perf"
    elif any("fix" in p or "bug" in p for p in paths):
        return "fix"
    elif any("feat" in p or "feature" in p for p in paths):
        return "feat"
    else:
        # Default based on change size
        total_changes = sum(f.added + f.removed for f in files)
        if total_changes < 10:
            return "chore"
        elif total_changes < 50:
            return "refactor"
        else:
            return "feat"


def analyze_changes(numstats: list[NumStat], contents:str) -> DiffSummary:
    if not numstats:
        raise ValueError("No changes to analyze")
    
    files = []
    total_added = 0
    total_removed = 0
    
    for stat in numstats:
        
        if stat.is_binary:
            continue
        
        
        if stat.added == 0 and stat.removed == 0:
            change_type = "renamed" if stat.is_renamed else "modified"
        elif stat.removed == 0:
            change_type = "added"
        elif stat.added == 0:
            change_type = "deleted"
        else:
            change_type = "modified"
        
        files.append(FileSummary(
            path=stat.file_path,
            added=stat.added,
            removed=stat.removed,
            change_type=change_type,
            old_path=stat.old_path
        ))
        
        total_added += stat.added
        total_removed += stat.removed
    
    if not files:
        raise ValueError("No non-binary files to analyze")
    
    # Determine the overall change type
    change_type = _determine_change_type(files)
    
    return DiffSummary(
        files=files,
        total_added=total_added,
        total_removed=total_removed,
        contents=contents,
        change_type=change_type,
    )


def build_prompt(summary: DiffSummary) -> str:
    prompt = f"""Generate a conventional commit message for these changes:

Type: {summary.change_type}
Files: {summary.total_files} files changed
Stats: +{summary.total_added}/-{summary.total_removed} lines
Diff Patch: {summary.contents}
Files changed:
"""
    
    significant = summary.significant_files
    other_files = [f for f in summary.files if f not in significant]
    
    for file in significant[:10]:
        change_desc = ""
        if file.change_type == "added":
            change_desc = " (new)"
        elif file.change_type == "deleted":
            change_desc = " (deleted)"
        elif file.change_type == "renamed":
            change_desc = f" (renamed from {file.old_path})"
        
        prompt += f"- {file.path}: +{file.added}/-{file.removed}{change_desc}\n"
    
    if other_files:
        prompt += f"- ... and {len(other_files)} other files with minor changes\n"
    
    prompt += """
Generate a conventional commit message:
- Format: <type>(<scope>): <subject>
- Body: explain what and why (2-3 lines max)
Return only the commit message."""
    
    return prompt
