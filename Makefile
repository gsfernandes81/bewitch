# make dev      uv sync: the locked pytest and hypothesis into .venv
# make test     the pytest suite
# make check    the same thing — .githooks/checks.sh is the one runner, so
#               what a push gets checked with is what you just ran
# make lint     ruff — the one on PATH if there is one (Termux ships a native
#               build; uv cannot install ruff on Android), else the locked one
# make gallery  python -m bewitch: every piece, drawn in this terminal
# make golden   rewrite the reference renders after a deliberate visual change

dev:
	uv sync

test: check

check:
	bash .githooks/checks.sh

lint:
	@if command -v ruff >/dev/null 2>&1; then ruff check . && ruff format --check .; \
	else uv run --group lint ruff check . && uv run --group lint ruff format --check .; fi

gallery:
	python3 -m bewitch

golden:
	BEWITCH_UPDATE_GOLDEN=1 bash .githooks/checks.sh

.PHONY: dev test check lint gallery golden
