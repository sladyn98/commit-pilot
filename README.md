# EdgeCommit MVP

AI-powered git commit message generator with smart diff filtering and resilient UX.

[![CI](https://github.com/yourusername/edgecommit/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/edgecommit/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🤖 **Smart AI commits**: Generates conventional commit messages using OpenAI
- 🔍 **Intelligent filtering**: Skips generated files, binaries, and lock files
- ⚡ **Fast processing**: <250ms for 10k-line diffs, uses `git diff --numstat`
- 🛡️ **Resilient UX**: Falls back to editor on any failure
- 🔒 **Secret redaction**: Automatically redacts API keys and tokens
- 📊 **Token management**: Hard 8k token limit with smart file trimming

## Installation

```bash
pip install edgecommit
```

## Quick Start

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. Stage your changes:
```bash
git add .
```

3. Generate and create commit:
```bash
edgecommit
```

## Configuration

Only 3 environment variables for MVP:

```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional (with defaults)
export FILTER_EXTRA_IGNORE="*.tmp,custom/"  # Extra files to ignore
export MAX_PROMPT_TOKENS="8000"             # Token limit
export EDGE_TELEMETRY="true"                # Anonymous metrics (opt-out)
```

## Usage

```bash
# Generate and create commit
edgecommit

# Preview only (no commit)
edgecommit --dry-run
```

### Resilient Design

EdgeCommit never blocks your workflow:
- **API failures** → Falls back to editor with helpful template
- **Network issues** → Opens editor with analyzed changes
- **Config errors** → Provides clear error messages
- **Any exception** → Editor fallback with error context

## Development

### Setup

```bash
git clone https://github.com/yourusername/edgecommit.git
cd edgecommit
poetry install
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=edgecommit

# Performance benchmarks
poetry run pytest tests/test_benchmark.py -v

# Lint
poetry run ruff check .
```

### MVP Architecture

```
edgecommit/
├── cli.py              # Entry point + editor fallback
├── config.py           # 3 env vars only
├── core/
│   ├── git.py          # git diff --numstat parsing
│   ├── filters.py      # Aggressive file filtering
│   ├── analyzer.py     # Basic file summaries
│   └── redaction.py    # Secret redaction
└── llm/
    └── openai.py       # Token counting + 8k limit
```

## Benchmarks

- **10k-line diff processing**: <250ms (M-series Mac)
- **Token usage**: ~100 tokens (vs 1000+ naive approach)
- **File filtering**: 80% reduction in processed content
- **Memory usage**: Linear scaling with file count

## License

MIT