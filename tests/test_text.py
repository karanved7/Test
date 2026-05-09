from click.testing import CliRunner
from cli.commands.text import text

runner = CliRunner()


def test_count_lines_words_chars():
    result = runner.invoke(text, ["count", "-"], input="hello world\nfoo\n")
    assert result.exit_code == 0
    assert "lines: 2" in result.output
    assert "words: 3" in result.output
    assert "chars: 16" in result.output


def test_count_empty_input():
    result = runner.invoke(text, ["count", "-"], input="")
    assert result.exit_code == 0
    assert "lines: 0" in result.output
    assert "words: 0" in result.output
    assert "chars: 0" in result.output


def test_count_from_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("one two\nthree\n")
    result = runner.invoke(text, ["count", str(f)])
    assert result.exit_code == 0
    assert "lines: 2" in result.output
    assert "words: 3" in result.output


def test_transform_upper():
    result = runner.invoke(text, ["transform", "--upper", "hello world"])
    assert result.exit_code == 0
    assert "HELLO WORLD" in result.output


def test_transform_lower():
    result = runner.invoke(text, ["transform", "--lower", "HELLO WORLD"])
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_transform_title():
    result = runner.invoke(text, ["transform", "--title", "hello world"])
    assert result.exit_code == 0
    assert "Hello World" in result.output


def test_transform_reverse():
    result = runner.invoke(text, ["transform", "--reverse", "hello"])
    assert result.exit_code == 0
    assert "olleh" in result.output


def test_transform_slug():
    result = runner.invoke(text, ["transform", "--slug", "Hello World Example"])
    assert result.exit_code == 0
    assert "hello-world-example" in result.output


def test_transform_no_mode_exits_nonzero():
    result = runner.invoke(text, ["transform", "hello"])
    assert result.exit_code != 0
