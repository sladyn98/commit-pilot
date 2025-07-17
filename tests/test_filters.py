import pytest

from edgecommit.config import Config
from edgecommit.core.filters import DiffFilter


class TestDiffFilter:
    @pytest.fixture
    def config(self):
        return Config()
    
    @pytest.fixture
    def diff_filter(self, config):
        return DiffFilter(config)
    
    def test_should_skip_binary_files(self, diff_filter):
        assert diff_filter.should_skip_file("image.png")
        assert diff_filter.should_skip_file("font.woff2")
        assert diff_filter.should_skip_file("document.pdf")
        assert diff_filter.should_skip_file("archive.zip")
    
    def test_should_skip_lock_files(self, diff_filter):
        assert diff_filter.should_skip_file("package-lock.json")
        assert diff_filter.should_skip_file("yarn.lock")
        assert diff_filter.should_skip_file("Pipfile.lock")
        assert diff_filter.should_skip_file("poetry.lock")
    
    def test_should_skip_compiled_files(self, diff_filter):
        assert diff_filter.should_skip_file("main.pyc")
        assert diff_filter.should_skip_file("App.class")
        assert diff_filter.should_skip_file("script.min.js")
        assert diff_filter.should_skip_file("style.min.css")
    
    def test_should_skip_build_directories(self, diff_filter):
        assert diff_filter.should_skip_file("dist/main.js")
        assert diff_filter.should_skip_file("build/index.html")
        assert diff_filter.should_skip_file("target/release/binary")
        assert diff_filter.should_skip_file("out/production/Main.class")
    
    def test_should_skip_dependency_directories(self, diff_filter):
        assert diff_filter.should_skip_file("node_modules/package/index.js")
        assert diff_filter.should_skip_file("vendor/library/src.php")
        assert diff_filter.should_skip_file(".venv/lib/python3.11/site-packages/module.py")
        assert diff_filter.should_skip_file("__pycache__/module.cpython-311.pyc")
    
    def test_should_not_skip_source_files(self, diff_filter):
        assert not diff_filter.should_skip_file("src/main.py")
        assert not diff_filter.should_skip_file("lib/utils.js")
        assert not diff_filter.should_skip_file("test/test_main.py")
        assert not diff_filter.should_skip_file("README.md")
        assert not diff_filter.should_skip_file("package.json")
    
    def test_extra_ignore_patterns(self):
        config = Config(filter_extra_ignore="*.tmp,custom/")
        diff_filter = DiffFilter(config)
        
        assert diff_filter.should_skip_file("temp.tmp")
        assert diff_filter.should_skip_file("custom/file.py")
        assert not diff_filter.should_skip_file("regular.py")
    
    def test_filter_diff_removes_ignored_files(self, diff_filter):
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
 
+Updated docs
