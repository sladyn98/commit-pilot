import time
from unittest.mock import Mock

import unittest

from config import Config
from core.analyzer import analyze_changes
from core.filters import DiffFilter
from core.git import NumStat


def generate_large_numstat(num_files: int = 100) -> list[NumStat]:
    stats = []
    for i in range(num_files):
        stats.append(NumStat(
            added=50 + i,
            removed=25 + i,
            file_path=f"src/module_{i:03d}.py",
            is_binary=False,
            is_renamed=False,
            old_path=None
        ))
    return stats


class TestPerformanceBenchmark(unittest.TestCase):
    
    def test_filter_performance(self):
        config = Config()
        diff_filter = DiffFilter(config)
        
        
        file_paths = [f"src/file_{i:04d}.py" for i in range(1000)]
        
        start_time = time.time()
        
        
        filtered = [path for path in file_paths if not diff_filter.should_skip_file(path)]
        
        end_time = time.time()
        duration = end_time - start_time
        
        
        self.assertLess(duration, 0.05, f"Filtering too slow: {duration:.3f}s")
        self.assertEqual(len(filtered), 1000)  
    
    def test_analyze_large_changeset(self):
        numstats = generate_large_numstat(100)
        
        start_time = time.time()
        
        summary = analyze_changes(numstats, "diff content")
        
        end_time = time.time()
        duration = end_time - start_time
        
        
        self.assertLess(duration, 0.1, f"Analysis too slow: {duration:.3f}s")
        self.assertEqual(summary.total_files, 100)
        self.assertGreater(summary.total_added, 0)
        self.assertGreater(summary.total_removed, 0)
    
    def test_end_to_end_processing_speed(self):
        config = Config()
        diff_filter = DiffFilter(config)
        
        
        numstats = [
            NumStat(added=45, removed=12, file_path="src/main.py", is_binary=False),
            NumStat(added=23, removed=8, file_path="src/utils.py", is_binary=False),
            NumStat(added=67, removed=34, file_path="src/auth.py", is_binary=False),
            NumStat(added=12, removed=5, file_path="tests/test_main.py", is_binary=False),
            NumStat(added=8, removed=3, file_path="README.md", is_binary=False),
            NumStat(added=156, removed=89, file_path="src/api.py", is_binary=False),
            NumStat(added=0, removed=0, file_path="package-lock.json", is_binary=False),  
            NumStat(added=34, removed=12, file_path="src/models.py", is_binary=False),
            NumStat(added=19, removed=7, file_path="src/config.py", is_binary=False),
            NumStat(added=78, removed=45, file_path="src/database.py", is_binary=False),
        ]
        
        start_time = time.time()
        
        
        filtered_numstats = [
            stat for stat in numstats 
            if not diff_filter.should_skip_file(stat.file_path)
        ]
        
        summary = analyze_changes(filtered_numstats, "diff content")
        
        end_time = time.time()
        duration = end_time - start_time
        
        
        self.assertLess(duration, 0.05, f"End-to-end processing too slow: {duration:.3f}s")
        self.assertEqual(summary.total_files, 9)
        self.assertNotIn("package-lock.json", [f.path for f in summary.files])
    
    def test_memory_usage_reasonable(self):
        
        numstats = generate_large_numstat(500)
        
        
        summary = analyze_changes(numstats, "diff content")
        
        
        self.assertEqual(summary.total_files, 500)
        
        
        sig_files = summary.significant_files
        self.assertGreater(len(sig_files), 0)
        self.assertTrue(all(f.added + f.removed > 5 for f in sig_files))
    
    def test_scalability(self):
        for num_files in [10, 50, 100, 500]:
            with self.subTest(num_files=num_files):
                numstats = generate_large_numstat(num_files)
                
                start_time = time.time()
                summary = analyze_changes(numstats, "diff content")
                duration = time.time() - start_time
                
                
                max_expected_duration = num_files * 0.001  
                self.assertLess(duration, max_expected_duration, f"Processing {num_files} files took {duration:.3f}s")
                self.assertEqual(summary.total_files, num_files)