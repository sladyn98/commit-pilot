import unittest

from core.analyzer import analyze_changes, build_prompt
from core.git import NumStat


class TestAnalyzer(unittest.TestCase):
    def test_analyze_changes_basic(self):
        numstats = [
            NumStat(added=10, removed=5, file_path="src/main.py", is_binary=False),
            NumStat(added=3, removed=1, file_path="tests/test_main.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats, "diff content")
        
        assert summary.total_files == 2
        assert summary.total_added == 13
        assert summary.total_removed == 6
        assert summary.change_type == "test"
        assert len(summary.files) == 2
    
    def test_build_prompt_basic(self):
        numstats = [
            NumStat(added=15, removed=8, file_path="src/feature.py", is_binary=False),
            NumStat(added=3, removed=2, file_path="tests/test_feature.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats, "diff content")
        prompt = build_prompt(summary)
        
        assert "Type: test" in prompt
        assert "Files: 2 files changed" in prompt
        assert "Stats: +18/-10 lines" in prompt
        assert "conventional commit message" in prompt.lower()
    
    def test_empty_changes_error(self):
        with self.assertRaises(ValueError):
            analyze_changes([], "diff content")