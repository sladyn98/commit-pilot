from dataclasses import dataclass
from typing import Literal

from edgecommit.core.git import NumStat

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
    
    @property
    def total_files(self) -> int:
        return len(self.files)
    
    @property
    def significant_files(self) -> list[FileSummary]:
        return [f for f in self.files if (f.added + f.removed) > 5]


def _classify_change_type(files: list[FileSummary]) -> ChangeType:
    paths = [f.path for f in files]
    
    
    if any("test" in p.lower() or "spec" in p.lower() for p in paths):
        return "test"
    
    
    if any(p.endswith((".md", ".rst", ".txt", ".mdx")) for p in paths):
        return "docs"
    
    
    if any(p.endswith((".css", ".scss", ".sass", ".less", ".styl")) for p in paths):
        return "style"
    
    
    if any(f.change_type == "added" for f in files):
        return "feat"
    
    
    if any(f.change_type == "deleted" for f in files):
        return "chore"
    
    
    if any(f.change_type == "renamed" for f in files):
        return "refactor"
    
    
    if len(files) > 10:
        return "refactor"
    elif len(files) > 5:
        return "chore"
    else:
        return "feat"


def analyze_changes(numstats: list[NumStat]) -> DiffSummary:
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
    
    change_type = _classify_change_type(files)
    
    return DiffSummary(
        files=files,
        total_added=total_added,
        total_removed=total_removed,
        change_type=change_type
    )


def build_prompt(summary: DiffSummary) -> str:
    prompt = f"""Generate a conventional commit message for these changes:

Type: {summary.change_type}
Files: {summary.total_files} files changed
Stats: +{summary.total_added}/-{summary.total_removed} lines

Files changed:
