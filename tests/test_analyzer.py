import pytest

from edgecommit.core.analyzer import DiffStats, DiffSummary, FileDiff, analyze_diff


class TestAnalyzeDiff:
    def test_empty_diff_raises_error(self):
        with pytest.raises(ValueError, match="Empty diff provided"):
            analyze_diff("")

    def test_single_file_addition(self):
        diff = """diff --git a/src/main.py b/src/main.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/src/main.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello, World!")
+    return True"""
        
        result = analyze_diff(diff)
        
        assert result.stats.files_changed == 1
        assert result.stats.insertions == 3
        assert result.stats.deletions == 0
        assert len(result.files) == 1
        assert result.files[0].path == "src/main.py"
        assert result.files[0].is_new is True
        assert result.files[0].additions == 3
        assert result.change_type == "feat"
        assert "Added src/main.py" in result.primary_changes

    def test_file_deletion(self):
        diff = """diff --git a/old_file.py b/old_file.py
deleted file mode 100644
index 1234567..0000000
--- a/old_file.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def old_function():
-    pass"""
        
        result = analyze_diff(diff)
        
        assert result.stats.files_changed == 1
        assert result.stats.insertions == 0
        assert result.stats.deletions == 2
        assert result.files[0].is_deleted is True
        assert "Deleted old_file.py" in result.primary_changes

    def test_file_modification(self):
        diff = """diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -1,3 +1,4 @@
 def existing():
-    return False
+    
+    return True
+    
        
        result = analyze_diff(diff)
        
        assert result.stats.files_changed == 1
        assert result.stats.insertions == 3
        assert result.stats.deletions == 1
        assert result.change_type == "fix"  

    def test_multiple_files(self):
        diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 def func1():
+    
     pass
diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,2 @@
+def func2():
+    pass"""
        
        result = analyze_diff(diff)
        
        assert result.stats.files_changed == 2
        assert result.stats.insertions == 3
        assert result.stats.deletions == 0
        assert len(result.files) == 2

    def test_test_file_classification(self):
        diff = """diff --git a/tests/test_feature.py b/tests/test_feature.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/tests/test_feature.py
@@ -0,0 +1,3 @@
+def test_something():
+    assert True
+    pass"""
        
        result = analyze_diff(diff)
        assert result.change_type == "test"

    def test_docs_classification(self):
        diff = """diff --git a/README.md b/README.md
index 1234567..abcdefg 100644
--- a/README.md
+++ b/README.md
@@ -1,1 +1,2 @@
 
+Documentation update"""
        
        result = analyze_diff(diff)
        assert result.change_type == "docs"

    def test_style_classification(self):
        diff = """diff --git a/styles.css b/styles.css
index 1234567..abcdefg 100644
--- a/styles.css
+++ b/styles.css
@@ -1,1 +1,2 @@
 .class { color: red; }
+.new-class { color: blue; }"""
        
        result = analyze_diff(diff)
        assert result.change_type == "style"

    def test_file_rename(self):
        diff = """diff --git a/old_name.py b/new_name.py
similarity index 100%
rename from old_name.py
rename to new_name.py"""
        
        result = analyze_diff(diff)
        
        assert len(result.files) == 1
        assert result.files[0].is_renamed is False  
        assert result.files[0].path == "new_name.py"