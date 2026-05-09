# CLI Toolkit

A general-purpose command-line toolkit written in Python. Provides file inspection, recursive search, and text transformation utilities.

## Install

```bash
pip install -e .
```

This installs the `toolkit` command.  
Alternatively, run without installing: `python -m cli <command>`.

## Commands

### `files stats <path>`

Show size, type, modification time, and line count for a file or directory.

```bash
toolkit files stats README.md
toolkit files stats .
```

### `files search <pattern> <path>`

Recursively search for a regex pattern across files.

```bash
toolkit files search "def " .                  # find all function definitions
toolkit files search "TODO" . --include "*.py" # only search Python files
toolkit files search "Error" . --case-sensitive
```

### `text count <file>`

Count lines, words, and characters (reads stdin if no file given).

```bash
toolkit text count README.md
cat README.md | toolkit text count -
```

### `text transform <text>`

Transform a string with one of the available modes.

```bash
toolkit text transform --upper  "hello world"   # HELLO WORLD
toolkit text transform --lower  "HELLO WORLD"   # hello world
toolkit text transform --title  "hello world"   # Hello World
toolkit text transform --reverse "hello"        # olleh
toolkit text transform --slug   "Hello World"   # hello-world
```

## Development

```bash
pip install -e .
pip install pytest
python -m pytest tests/ -v
```

## Project Layout

```
├── cli/
│   ├── main.py            # entry point, Click group
│   ├── __main__.py        # enables `python -m cli`
│   └── commands/
│       ├── files.py       # stats, search
│       └── text.py        # count, transform
├── tests/
│   ├── test_files.py
│   └── test_text.py
├── pyproject.toml
└── requirements.txt
```
