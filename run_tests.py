#!/usr/bin/env python3

import subprocess
import sys

def run_command(cmd):
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print('='*60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    return result.returncode == 0

def main():
    
    if run_command("python -m pytest --version"):
        print("\nRunning tests with pytest...")
        success = run_command("python -m pytest tests/ -v")
        if not success:
            print("\nTests failed!")
            sys.exit(1)
    else:
        print("\nPytest not found. Running basic import checks...")
        
        try:
            import edgecommit
            print(f"✓ edgecommit package imported successfully (version: {edgecommit.__version__})")
            
            from edgecommit import cli, config
            print("✓ CLI and config modules imported")
            
            from edgecommit.core import git, analyzer
            print("✓ Core modules imported")
            
            from edgecommit.llm import get_provider
            print("✓ LLM modules imported")
            
            print("\nAll imports successful!")
        except Exception as e:
            print(f"\n✗ Import error: {e}")
            sys.exit(1)
    
    print("\n✓ All checks passed!")

if __name__ == "__main__":
    main()