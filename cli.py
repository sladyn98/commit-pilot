import os
import subprocess
import tempfile
import time

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import Config
from core import analyzer, git
from core.filters import DiffFilter
from core.redaction import SecretRedactor
from llm.openai import OpenAIProvider

app = typer.Typer(
    name="edgecommit",
    help="AI-powered git commit message generator",
    no_args_is_help=False,
)
console = Console()


def fallback_to_editor(template: str = None) -> str:
    if template is None:
        template = git.get_editor_fallback_template()
    
    editor = os.getenv("EDITOR", "nano")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(template)
        temp_file = f.name
    
    try:
        subprocess.run([editor, temp_file], check=True)
        
        with open(temp_file, 'r') as f:
            content = f.read()
        
        lines = []
        for line in content.split('\n'):
            if line.strip() and not line.strip().startswith('#'):
                lines.append(line)
        
        message = '\n'.join(lines).strip()
        
        if not message:
            raise ValueError("Empty commit message")
        
        return message
        
    finally:
        os.unlink(temp_file)


@app.command()
def main(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Show commit message without creating commit",
    ),
) -> None:
    start_time = time.time()
    
    try:
        config = Config()
        
        if not git.has_staged_changes():
            console.print("[red]✗[/red] No staged changes found. Run 'git add' first.")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing staged changes...", total=None)
            
            numstats = git.get_staged_numstat()
            if not numstats:
                console.print("[red]✗[/red] No changes found in staged files.")
                raise typer.Exit(1)
            
            progress.update(task, description="Processing changes...")
            
            diff_filter = DiffFilter(config)
            filtered_numstats = [
                stat for stat in numstats 
                if not diff_filter.should_skip_file(stat.file_path)
            ]
            
            if not filtered_numstats:
                console.print("[yellow]⚠[/yellow] All changed files are ignored. Nothing to commit.")
                raise typer.Exit(0)
            

            diff_patch = git.get_diff_patch()
            truncated_diff = diff_filter.parse_diff_patch_file(diff_patch)
            print(truncated_diff)
            summary = analyzer.analyze_changes(filtered_numstats, truncated_diff)
            progress.update(task, description="Generating commit message...")
            
            try:
                llm = OpenAIProvider(config)
                commit_msg = llm.generate_commit(summary)
                
                redactor = SecretRedactor()
                if redactor.has_potential_secrets(commit_msg):
                    commit_msg = redactor.redact_diff(commit_msg)
                
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] AI generation failed: {e}")
                console.print("[yellow]→[/yellow] Falling back to editor...")
                
                template = f"""# Auto-commit fallback - AI generation failed
# 
# Error: {str(e)}
# 
# Analyzed changes:
# Type: {summary.change_type}
# Files: {summary.total_files} files changed
# Stats: +{summary.total_added}/-{summary.total_removed} lines
#
# Files changed:
"""
                for file in summary.significant_files[:5]:
                    template += f"# - {file.path}: +{file.added}/-{file.removed}\n"
                
                template += """#
# Please write a conventional commit message:
# Format: <type>(<scope>): <subject>
#
# Types: feat, fix, docs, style, refactor, perf, test, chore

"""
                
                commit_msg = fallback_to_editor(template)
        
        processing_time = time.time() - start_time
        
        console.print(f"\n[bold cyan]Generated commit message:[/bold cyan] [dim]({processing_time:.2f}s)[/dim]")
        console.print(f"[green]{commit_msg}[/green]\n")
        
        if summary.total_files > 1:
            console.print(f"[dim]Files: {summary.total_files} changed (+{summary.total_added}/-{summary.total_removed})[/dim]")
        
        if dry_run:
            console.print("[yellow]ℹ[/yellow] Dry run mode - no commit created")
        else:
            if typer.confirm("Create commit with this message?", default=True):
                git.create_commit(commit_msg)
                console.print("[green]✓[/green] Commit created successfully!")
            else:
                console.print("[yellow]ℹ[/yellow] Commit cancelled")
                
    except git.GitError as e:
        console.print(f"[red]✗ Git error:[/red] {e}")
        console.print("[yellow]→[/yellow] Falling back to editor...")
        try:
            commit_msg = fallback_to_editor()
            git.create_commit(commit_msg)
            console.print("[green]✓[/green] Commit created via editor!")
        except Exception as fallback_error:
            console.print(f"[red]✗ Editor fallback failed:[/red] {fallback_error}")
            raise typer.Exit(1)
        
    except ValueError as e:
        console.print(f"[red]✗ Configuration error:[/red] {e}")
        raise typer.Exit(1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]ℹ[/yellow] Interrupted by user")
        raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        console.print("[yellow]→[/yellow] Falling back to editor...")
        try:
            commit_msg = fallback_to_editor()
            git.create_commit(commit_msg)
            console.print("[green]✓[/green] Commit created via editor!")
        except Exception as fallback_error:
            console.print(f"[red]✗ Editor fallback failed:[/red] {fallback_error}")
            raise typer.Exit(1)


@app.callback()
def callback() -> None:
    pass


if __name__ == "__main__":
    app()