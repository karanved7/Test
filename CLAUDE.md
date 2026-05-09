# CLAUDE.md

This file documents the repository structure, conventions, and workflows for AI assistants (Claude Code and others) working in this codebase.

## Repository Overview

- **Repo**: `karanved7/Test` on GitHub
- **State**: Newly initialized — currently contains only a `README.md`
- **Purpose**: Test / sandbox repository

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code |
| `claude/<description>-<id>` | AI-assisted feature or task branches |

- All development must happen on a designated feature branch.
- Never push directly to `main` without a pull request.
- Branch names for AI tasks follow the pattern `claude/<short-description>-<random-id>`.

## Git Workflow

```bash
# Develop on the designated branch
git checkout -b claude/<description>-<id>

# Stage and commit with clear messages
git add <specific-files>
git commit -m "feat: describe what and why"

# Push with tracking
git push -u origin <branch-name>
```

### Commit Message Conventions

- Use the imperative mood: "add", "fix", "update", "remove"
- Keep the subject line under 72 characters
- Focus on *why*, not *what*
- Do not reference issue numbers or PR links in the subject line

Good examples:
```
feat: add user authentication module
fix: prevent nil pointer dereference on empty config
docs: document branch strategy in CLAUDE.md
```

## File Structure

```
/
├── README.md       # Project overview (currently placeholder)
└── CLAUDE.md       # This file — AI assistant guidance
```

As the project grows, update this section to reflect the actual directory layout.

## Development Conventions

### General

- Prefer editing existing files over creating new ones
- Do not add comments that explain *what* code does — only explain *why* when it is non-obvious
- No half-finished implementations; complete what you start or leave the original code untouched
- Do not add error handling for scenarios that cannot happen
- Do not introduce abstractions beyond what the current task requires

### Security

- Never commit secrets, credentials, `.env` files, or API keys
- Validate input at system boundaries (user input, external APIs); trust internal code
- Avoid common vulnerabilities: command injection, XSS, SQL injection, OWASP Top 10

### Pull Requests

- Create a PR only when explicitly requested
- PR title: concise, under 70 characters
- PR body: summary bullets + test plan checklist
- Do not force-push to `main`

## AI Assistant Notes

- **Working directory**: `/home/user/Test`
- **Default development branch**: `claude/add-claude-documentation-fGExQ` (update per task)
- Always read a file before editing it
- Run `git status` before committing to avoid staging unintended files
- Use `git push -u origin <branch>` — retry up to 4 times with exponential backoff on network failure
- Do not create a pull request unless the user explicitly asks

## Updating This File

Whenever the repository structure, tooling, or conventions change materially, update this file as part of that same commit so it stays accurate.
