There is a script to take screenshots. This is useful for vaguely testing what is going on.
This uses playwright.

# Testing

Run `./run-tests` - spins up isolated server on port 5099 in /tmp, runs all tests, cleans up. Uses `.venv-release` (created by first `./release` run). Note: `./release` runs the full test suite automatically, so running tests separately is optional.

# Releasing and deploying

1. Bump version in `pyproject.toml`
2. Commit all changes (release script requires clean working tree)
3. Run `./release` — runs full test suite, pushes to git, tags, builds, uploads to PyPI
4. Run `./deploy/deploy` — SSHs to the server, pip upgrades, restarts the systemd service

**PyPI cache issue:** Sometimes the first deploy after release shows "NO NEW VERSION INSTALLED" because PyPI's CDN hasn't propagated yet. Just wait ~30 seconds and run `./deploy/deploy` again.

# Local development

The app is installed locally with `pipx install -e .` so code changes take effect without reinstalling (unless there are new dependencies or entrypoints in pyproject.toml).

Run `./dev-server` to (re)start the local dev server on port 9876. It kills any existing instance first.
