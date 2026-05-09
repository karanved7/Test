from click.testing import CliRunner
from cli.commands.files import files

runner = CliRunner()


def test_stats_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("line1\nline2\nline3\n")
    result = runner.invoke(files, ["stats", str(f)])
    assert result.exit_code == 0
    assert "hello.txt" in result.output
    assert "lines:    3" in result.output


def test_stats_directory_counts_files(tmp_path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.txt").write_text("world")
    result = runner.invoke(files, ["stats", str(tmp_path)])
    assert result.exit_code == 0
    assert "files:    2" in result.output
    assert "dirs:     0" in result.output


def test_stats_directory_counts_subdirs(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("x")
    result = runner.invoke(files, ["stats", str(tmp_path)])
    assert result.exit_code == 0
    assert "dirs:     1" in result.output


def test_search_finds_match(tmp_path):
    (tmp_path / "foo.txt").write_text("hello world\nfoo bar\n")
    result = runner.invoke(files, ["search", "foo", str(tmp_path)])
    assert result.exit_code == 0
    assert "foo bar" in result.output


def test_search_is_case_insensitive_by_default(tmp_path):
    (tmp_path / "a.txt").write_text("Hello World\n")
    result = runner.invoke(files, ["search", "hello", str(tmp_path)])
    assert result.exit_code == 0
    assert "Hello World" in result.output


def test_search_case_sensitive_flag(tmp_path):
    (tmp_path / "a.txt").write_text("Hello World\n")
    result = runner.invoke(files, ["search", "--case-sensitive", "hello", str(tmp_path)])
    assert "No matches found." in result.output


def test_search_no_match(tmp_path):
    (tmp_path / "a.txt").write_text("nothing here\n")
    result = runner.invoke(files, ["search", "xyz123", str(tmp_path)])
    assert "No matches found." in result.output


def test_search_include_filter(tmp_path):
    (tmp_path / "a.py").write_text("target line\n")
    (tmp_path / "b.txt").write_text("target line\n")
    result = runner.invoke(files, ["search", "--include", "*.py", "target", str(tmp_path)])
    assert result.exit_code == 0
    assert "a.py" in result.output
    assert "b.txt" not in result.output


def test_search_invalid_regex(tmp_path):
    result = runner.invoke(files, ["search", "[invalid", str(tmp_path)])
    assert result.exit_code != 0
    assert "Invalid regex" in result.output
