import re
from datetime import datetime
from pathlib import Path

import click


@click.group()
def files():
    """File and directory utilities."""
    pass


@files.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def stats(path):
    """Show stats for a file or directory."""
    p = Path(path)
    if p.is_file():
        size = p.stat().st_size
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"name:     {p.name}")
        click.echo(f"type:     file")
        click.echo(f"size:     {_human_size(size)}")
        click.echo(f"modified: {mtime}")
        try:
            line_count = len(p.read_text(errors="replace").splitlines())
            click.echo(f"lines:    {line_count}")
        except PermissionError:
            pass
    else:
        total_size = 0
        file_count = 0
        dir_count = 0
        for entry in p.rglob("*"):
            if entry.is_file():
                total_size += entry.stat().st_size
                file_count += 1
            elif entry.is_dir():
                dir_count += 1
        click.echo(f"path:     {p.resolve()}")
        click.echo(f"type:     directory")
        click.echo(f"files:    {file_count}")
        click.echo(f"dirs:     {dir_count}")
        click.echo(f"size:     {_human_size(total_size)}")


@files.command()
@click.argument("pattern")
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--case-sensitive", "-c", is_flag=True, default=False)
@click.option("--include", "-i", default="*", help="File glob filter, e.g. '*.py'")
def search(pattern, path, case_sensitive, include):
    """Search for PATTERN in files under PATH."""
    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as exc:
        raise click.BadParameter(f"Invalid regex: {exc}", param_hint="PATTERN")

    p = Path(path)
    found = False
    for file in sorted(p.rglob(include)):
        if not file.is_file():
            continue
        try:
            content = file.read_text(errors="replace")
        except PermissionError:
            continue
        for lineno, line in enumerate(content.splitlines(), 1):
            if regex.search(line):
                click.echo(f"{file}:{lineno}: {line.rstrip()}")
                found = True

    if not found:
        click.echo("No matches found.", err=True)


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
