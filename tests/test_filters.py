import unittest

from config import Config
from core.filters import DiffFilter


class TestDiffFilter(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.diff_filter = DiffFilter(self.config)
    
    def test_should_skip_binary_files(self):
        self.assertTrue(self.diff_filter.should_skip_file("image.png"))
        self.assertTrue(self.diff_filter.should_skip_file("font.woff2"))
        self.assertTrue(self.diff_filter.should_skip_file("document.pdf"))
        self.assertTrue(self.diff_filter.should_skip_file("archive.zip"))
    
    def test_should_skip_lock_files(self):
        self.assertTrue(self.diff_filter.should_skip_file("package-lock.json"))
        self.assertTrue(self.diff_filter.should_skip_file("yarn.lock"))
        self.assertTrue(self.diff_filter.should_skip_file("Pipfile.lock"))
        self.assertTrue(self.diff_filter.should_skip_file("poetry.lock"))
    
    def test_should_not_skip_source_files(self):
        self.assertFalse(self.diff_filter.should_skip_file("src/main.py"))
        self.assertFalse(self.diff_filter.should_skip_file("lib/utils.js"))
        self.assertFalse(self.diff_filter.should_skip_file("test/test_main.py"))
        self.assertFalse(self.diff_filter.should_skip_file("README.md"))
    
    def test_filter_diff_removes_ignored_files(self):
        diff_content = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
+    print("Hello")
     pass
diff --git a/package-lock.json b/package-lock.json
index 1234567..abcdefg 100644
--- a/package-lock.json
+++ b/package-lock.json
@@ -1,10 +1,10 @@
 {
   "name": "test",
-  "version": "1.0.0"
+  "version": "1.0.1"
 }
diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,1 +1,2 @@
 # Project
+Updated docs
"""
        
        filtered = self.diff_filter.filter_diff(diff_content)
        
        # Should contain main.py and README.md but not package-lock.json
        self.assertIn("src/main.py", filtered)
        self.assertIn("README.md", filtered)
        self.assertNotIn("package-lock.json", filtered)