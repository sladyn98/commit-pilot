import unittest

from edgecommit.core.analyzer import FileSummary, analyze_changes, build_prompt
from edgecommit.core.git import NumStat


class TestAnalyzerMVP(unittest.TestCase):
    def test_analyze_changes_basic(self):
        numstats = [
            NumStat(added=10, removed=5, file_path="src/main.py", is_binary=False),
            NumStat(added=3, removed=1, file_path="tests/test_main.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats)
        
        self.assertEqual(summary.total_files, 2)
        self.assertEqual(summary.total_added, 13)
        self.assertEqual(summary.total_removed, 6)
        self.assertEqual(summary.change_type, "test")
        self.assertEqual(len(summary.files), 2)
    
    def test_analyze_changes_skips_binary(self):
        numstats = [
            NumStat(added=10, removed=5, file_path="src/main.py", is_binary=False),
            NumStat(added=0, removed=0, file_path="image.png", is_binary=True),
        ]
        
        summary = analyze_changes(numstats)
        
        self.assertEqual(summary.total_files, 1)
        self.assertEqual(summary.files[0].path, "src/main.py")
    
    def test_analyze_changes_classifies_types(self):
        
        test_stats = [NumStat(added=10, removed=5, file_path="test_feature.py", is_binary=False)]
        self.assertEqual(analyze_changes(test_stats).change_type, "test")
        
        
        doc_stats = [NumStat(added=10, removed=5, file_path="README.md", is_binary=False)]
        self.assertEqual(analyze_changes(doc_stats).change_type, "docs")
        
        
        style_stats = [NumStat(added=10, removed=5, file_path="styles.css", is_binary=False)]
        self.assertEqual(analyze_changes(style_stats).change_type, "style")
        
        
        new_stats = [NumStat(added=10, removed=0, file_path="new_feature.py", is_binary=False)]
        summary = analyze_changes(new_stats)
        self.assertEqual(summary.change_type, "feat")
        self.assertEqual(summary.files[0].change_type, "added")
    
    def test_analyze_changes_handles_renames(self):
        numstats = [
            NumStat(
                added=0,
                removed=0,
                file_path="new_name.py",
                is_binary=False,
                is_renamed=True,
                old_path="old_name.py"
            )
        ]
        
        summary = analyze_changes(numstats)
        
        self.assertEqual(summary.total_files, 1)
        self.assertEqual(summary.files[0].change_type, "renamed")
        self.assertEqual(summary.files[0].old_path, "old_name.py")
        self.assertEqual(summary.change_type, "refactor")
    
    def test_analyze_changes_handles_deletions(self):
        numstats = [
            NumStat(added=0, removed=50, file_path="deprecated.py", is_binary=False)
        ]
        
        summary = analyze_changes(numstats)
        
        self.assertEqual(summary.files[0].change_type, "deleted")
        self.assertEqual(summary.change_type, "chore")
    
    def test_significant_files_identification(self):
        numstats = [
            NumStat(added=50, removed=20, file_path="major_change.py", is_binary=False),
            NumStat(added=2, removed=1, file_path="minor_change.py", is_binary=False),
            NumStat(added=100, removed=30, file_path="huge_change.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats)
        significant = summary.significant_files
        
        
        self.assertEqual(len(significant), 2)
        self.assertTrue(any(f.path == "major_change.py" for f in significant))
        self.assertTrue(any(f.path == "huge_change.py" for f in significant))
        self.assertFalse(any(f.path == "minor_change.py" for f in significant))
    
    def test_build_prompt_basic(self):
        summary = analyze_changes([
            NumStat(added=15, removed=8, file_path="src/feature.py", is_binary=False),
            NumStat(added=3, removed=2, file_path="tests/test_feature.py", is_binary=False),
        ])
        
        prompt = build_prompt(summary)
        
        self.assertIn("Type: test", prompt)
        self.assertIn("Files: 2 files changed", prompt)
        self.assertIn("Stats: +18/-10 lines", prompt)
        self.assertIn("src/feature.py: +15/-8", prompt)
        self.assertIn("tests/test_feature.py: +3/-2", prompt)
        self.assertIn("conventional commit message", prompt.lower())
    
    def test_build_prompt_handles_many_files(self):
        numstats = []
        for i in range(15):
            numstats.append(NumStat(
                added=10 + i,
                removed=5 + i,
                file_path=f"src/file_{i:02d}.py",
                is_binary=False
            ))
        
        summary = analyze_changes(numstats)
        prompt = build_prompt(summary)
        
        
        self.assertLessEqual(prompt.count("src/file_"), 10)
        self.assertIn("other files with minor changes", prompt)
    
    def test_build_prompt_includes_change_descriptions(self):
        numstats = [
            NumStat(added=10, removed=0, file_path="new_file.py", is_binary=False),
            NumStat(added=0, removed=20, file_path="deleted_file.py", is_binary=False),
            NumStat(
                added=5,
                removed=5,
                file_path="renamed_file.py",
                is_binary=False,
                is_renamed=True,
                old_path="old_file.py"
            ),
        ]
        
        summary = analyze_changes(numstats)
        prompt = build_prompt(summary)
        
        self.assertIn("(new)", prompt)
        self.assertIn("(deleted)", prompt)
        self.assertIn("(renamed from old_file.py)", prompt)
    
    def test_empty_changes_error(self):
        with self.assertRaises(ValueError):
            analyze_changes([])
    
    def test_only_binary_files_error(self):
        numstats = [
            NumStat(added=0, removed=0, file_path="image.png", is_binary=True),
            NumStat(added=0, removed=0, file_path="document.pdf", is_binary=True),
        ]
        
        with self.assertRaises(ValueError):
            analyze_changes(numstats)