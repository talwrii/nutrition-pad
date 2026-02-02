There is a script to take screenshots. This is useful for vaguely testing what is going on.
This uses playwright.

# Releasing and deploying

1. Bump version in `pyproject.toml`
2. Run `./release` — runs tests, pushes to git, tags, builds, uploads to PyPI
3. Run `./deploy/deploy` — SSHs to the server, pip upgrades, restarts the systemd service

# Local development

The app is installed locally with `pipx install -e .` so code changes take effect without reinstalling (unless there are new dependencies or entrypoints in pyproject.toml).

A local server can be started with `nutrition-pad --port 9876`. Kill old instances first: `lsof -ti:9876 | xargs kill -9`.
