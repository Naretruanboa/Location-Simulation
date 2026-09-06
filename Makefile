SHELL := /bin/zsh

PYTHON ?= python3.11
VENV := .venv
PID_FILE := .run/server.pid
LOG_FILE := .run/server.log

.PHONY: install start stop status logs logs-follow test

install:
	@if [ ! -x "$(VENV)/bin/python" ]; then $(PYTHON) -m venv "$(VENV)"; fi
	@"$(VENV)/bin/python" -m pip install --upgrade pip
	@"$(VENV)/bin/python" -m pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

start:
	@if [ ! -x "$(VENV)/bin/python" ]; then echo "Virtual environment is missing. Run: make install"; exit 1; fi
	@if [ ! -f .env ]; then echo ".env is missing. Run: make install, then configure .env"; exit 1; fi
	@mkdir -p .run
	@set -a; source .env; set +a; \
	port="$${PORT:-8000}"; \
	pid="$$(lsof -tiTCP:"$$port" -sTCP:LISTEN | head -n 1)"; \
	if [ -n "$$pid" ]; then \
		echo "Server is already running on port $$port (PID $$pid)"; exit 0; \
	fi; \
	nohup "$(CURDIR)/$(VENV)/bin/python" "$(CURDIR)/app.py" > "$(CURDIR)/$(LOG_FILE)" 2>&1 & \
	pid=$$!; echo "$$pid" > "$(PID_FILE)"; \
	echo "Server started (PID $$pid). Open http://127.0.0.1:$$port"

stop:
	@if [ ! -f .env ]; then echo ".env is missing. Run: make install, then configure .env"; exit 1; fi
	@set -a; source .env; set +a; \
	port="$${PORT:-8000}"; pid=""; \
	if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat "$(PID_FILE)")" 2>/dev/null; then pid="$$(cat "$(PID_FILE)")"; fi; \
	if [ -z "$$pid" ]; then pid="$$(lsof -tiTCP:"$$port" -sTCP:LISTEN | head -n 1)"; fi; \
	if [ -z "$$pid" ]; then rm -f "$(PID_FILE)"; echo "Server is already stopped"; exit 0; fi; \
	command="$$(ps -p "$$pid" -o command=)"; cwd="$$(lsof -a -p "$$pid" -d cwd -Fn | sed -n 's/^n//p')"; \
	if [[ "$$cwd" == "$(CURDIR)" && "$$command" == *"app.py"* ]]; then \
		kill "$$pid"; rm -f "$(PID_FILE)"; echo "Stopping server (PID $$pid)"; \
	else echo "Refusing to stop PID $$pid: it is not this project's app.py"; exit 1; fi

status:
	@if [ ! -f .env ]; then echo ".env is missing. Run: make install, then configure .env"; exit 1; fi
	@set -a; source .env; set +a; \
	port="$${PORT:-8000}"; pid=""; \
	if [ -f "$(PID_FILE)" ] && kill -0 "$$(cat "$(PID_FILE)")" 2>/dev/null; then pid="$$(cat "$(PID_FILE)")"; fi; \
	if [ -z "$$pid" ]; then pid="$$(lsof -tiTCP:"$$port" -sTCP:LISTEN | head -n 1)"; fi; \
	if [ -n "$$pid" ]; then echo "Server is running on port $$port (PID $$pid)"; else echo "Server is stopped"; fi

logs:
	@if [ -f "$(LOG_FILE)" ]; then tail -n 200 "$(LOG_FILE)"; else echo "No server log yet. Run: make start"; fi

logs-follow:
	@if [ ! -f "$(LOG_FILE)" ]; then echo "No server log yet. Run: make start"; exit 1; fi
	@tail -n 200 -f "$(LOG_FILE)"

test:
	@"$(VENV)/bin/pytest" -q
