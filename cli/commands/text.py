import click


@click.group()
def text():
    """Text processing utilities."""
    pass


@text.command()
@click.argument("file", type=click.File("r"), default="-")
def count(file):
    """Count lines, words, and characters in FILE (or stdin)."""
    content = file.read()
    lines = len(content.splitlines())
    words = len(content.split())
    chars = len(content)
    click.echo(f"lines: {lines}")
    click.echo(f"words: {words}")
    click.echo(f"chars: {chars}")


@text.command()
@click.argument("input_text")
@click.option("--upper", "mode", flag_value="upper", help="Convert to UPPERCASE")
@click.option("--lower", "mode", flag_value="lower", help="Convert to lowercase")
@click.option("--title", "mode", flag_value="title", help="Convert to Title Case")
@click.option("--reverse", "mode", flag_value="reverse", help="Reverse the string")
@click.option("--slug", "mode", flag_value="slug", help="Convert to url-slug-format")
def transform(input_text, mode):
    """Transform INPUT_TEXT using the chosen mode."""
    if mode is None:
        raise click.UsageError(
            "Specify a transformation: --upper, --lower, --title, --reverse, or --slug"
        )
    transforms = {
        "upper": str.upper,
        "lower": str.lower,
        "title": str.title,
        "reverse": lambda s: s[::-1],
        "slug": lambda s: "-".join(s.lower().split()),
    }
    click.echo(transforms[mode](input_text))
