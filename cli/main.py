import click
from cli.commands.files import files
from cli.commands.text import text


@click.group()
@click.version_option("0.1.0")
def cli():
    """General-purpose CLI toolkit."""
    pass


cli.add_command(files)
cli.add_command(text)

if __name__ == "__main__":
    cli()
