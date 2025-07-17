import pytest

from edgecommit.core.analyzer import FileSummary, analyze_changes, build_prompt
from edgecommit.core.git import NumStat


class TestAnalyzerMVP:
    def test_analyze_changes_basic(self):
        numstats = [
            NumStat(added=10, removed=5, file_path="src/main.py", is_binary=False),
            NumStat(added=3, removed=1, file_path="tests/test_main.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats)
        
        assert summary.total_files == 2
        assert summary.total_added == 13
        assert summary.total_removed == 6
        assert summary.change_type == "test"  
        assert len(summary.files) == 2
    
    def test_analyze_changes_skips_binary(self):
        numstats = [
            NumStat(added=10, removed=5, file_path="src/main.py", is_binary=False),
            NumStat(added=0, removed=0, file_path="image.png", is_binary=True),
        ]
        
        summary = analyze_changes(numstats)
        
        assert summary.total_files == 1
        assert summary.files[0].path == "src/main.py"
    
    def test_analyze_changes_classifies_types(self):
        
        test_stats = [NumStat(added=10, removed=5, file_path="test_feature.py", is_binary=False)]
        assert analyze_changes(test_stats).change_type == "test"
        
        
        doc_stats = [NumStat(added=10, removed=5, file_path="README.md", is_binary=False)]
        assert analyze_changes(doc_stats).change_type == "docs"
        
        
        style_stats = [NumStat(added=10, removed=5, file_path="styles.css", is_binary=False)]
        assert analyze_changes(style_stats).change_type == "style"
        
        
        new_stats = [NumStat(added=10, removed=0, file_path="new_feature.py", is_binary=False)]
        summary = analyze_changes(new_stats)
        assert summary.change_type == "feat"
        assert summary.files[0].change_type == "added"
    
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
        
        assert summary.total_files == 1
        assert summary.files[0].change_type == "renamed"
        assert summary.files[0].old_path == "old_name.py"
        assert summary.change_type == "refactor"
    
    def test_analyze_changes_handles_deletions(self):
        numstats = [
            NumStat(added=0, removed=50, file_path="deprecated.py", is_binary=False)
        ]
        
        summary = analyze_changes(numstats)
        
        assert summary.files[0].change_type == "deleted"
        assert summary.change_type == "chore"
    
    def test_significant_files_identification(self):
        numstats = [
            NumStat(added=50, removed=20, file_path="major_change.py", is_binary=False),
            NumStat(added=2, removed=1, file_path="minor_change.py", is_binary=False),
            NumStat(added=100, removed=30, file_path="huge_change.py", is_binary=False),
        ]
        
        summary = analyze_changes(numstats)
        significant = summary.significant_files
        
        
        assert len(significant) == 2
        assert any(f.path == "major_change.py" for f in significant)
        assert any(f.path == "huge_change.py" for f in significant)
        assert not any(f.path == "minor_change.py" for f in significant)
    
    def test_build_prompt_basic(self):
        summary = analyze_changes([
            NumStat(added=15, removed=8, file_path="src/feature.py", is_binary=False),
            NumStat(added=3, removed=2, file_path="tests/test_feature.py", is_binary=False),
        ])
        
        prompt = build_prompt(summary)
        
        assert "Type: test" in prompt
        assert "Files: 2 files changed" in prompt
        assert "Stats: +18/-10 lines" in prompt
        assert "src/feature.py: +15/-8" in prompt
        assert "tests/test_feature.py: +3/-2" in prompt
        assert "conventional commit message" in prompt.lower()
    
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
        
        
        assert prompt.count("src/file_") <= 10
        assert "other files with minor changes" in prompt
    
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
        
        assert "(new)" in prompt
        assert "(deleted)" in prompt
        assert "(renamed from old_file.py)" in prompt
    
    def test_empty_changes_error(self):
        with pytest.raises(ValueError, match="No changes to analyze"):
            analyze_changes([])
    
    def test_only_binary_files_error(self):
        numstats = [
            NumStat(added=0, removed=0, file_path="image.png", is_binary=True),
            NumStat(added=0, removed=0, file_path="document.pdf", is_binary=True),
        ]
        
        with pytest.raises(ValueError, match="No non-binary files to analyze"):
            analyze_changes(numstats)