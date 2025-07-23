from abc import ABC, abstractmethod

from core.analyzer import DiffSummary


class BaseLLMProvider(ABC):
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    def generate_commit(self, diff_summary: DiffSummary) -> str:
        pass
    
    def _create_prompt(self, diff_summary: DiffSummary) -> str:
        return f"""Generate a conventional commit message for the following changes:

Change Type: {diff_summary.change_type}
Files Changed: {diff_summary.stats.files_changed}
Insertions: {diff_summary.stats.insertions}
Deletions: {diff_summary.stats.deletions}

Primary Changes:
{chr(10).join(f"- {change}" for change in diff_summary.primary_changes)}

Modified Files:
{chr(10).join(f"- {f.path} (+{f.additions}/-{f.deletions})" for f in diff_summary.files[:10])}

Generate a commit message following the Conventional Commits specification:
- Format: <type>(<scope>): <subject>
- Body: 2-3 lines explaining what and why (not how)
- Types: feat, fix, docs, style, refactor, perf, test, chore
- Keep subject under 50 characters
- Use imperative mood

Return ONLY the commit message, no explanations."""