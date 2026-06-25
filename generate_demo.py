import json
import time


class AsciicastGenerator:
    def __init__(self, filename, width=100, height=30):
        self.filename = filename
        self.width = width
        self.height = height
        self.time = 0.0
        self.events = []

    def add_event(self, event_type, data):
        self.events.append([self.time, event_type, data])

    def wait(self, duration):
        self.time += duration

    def type_command(self, prompt, command, typing_speed=0.08):
        self.add_event("o", prompt)
        self.wait(0.5)
        for char in command:
            self.add_event("o", char)
            self.wait(typing_speed)
        self.wait(0.5)
        self.add_event("o", "\r\n")

    def output_line(self, line, delay=0.05):
        self.add_event("o", line + "\r\n")
        self.wait(delay)

    def output_text(self, text, delay_per_char=0.0):
        if delay_per_char > 0:
            for char in text:
                self.add_event("o", char)
                self.wait(delay_per_char)
        else:
            self.add_event("o", text)

    def clear_screen(self):
        self.add_event("o", "\x1b[2J\x1b[H")
        self.wait(0.1)

    def save(self):
        with open(self.filename, 'w') as f:
            header = {
                "version": 2,
                "width": self.width,
                "height": self.height,
                "timestamp": int(time.time()),
                "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"}
            }
            f.write(json.dumps(header) + "\n")
            for event in self.events:
                f.write(json.dumps(event) + "\n")

# Settings
PROMPT = "\x1b[1;32muser@host\x1b[0m:\x1b[1;34m~\x1b[0m$ "
PROMPT_PROJ = "\x1b[1;32muser@host\x1b[0m:\x1b[1;34m~/sample-fastapi-project\x1b[0m$ "

gen = AsciicastGenerator("decisiondrift_demo.cast", width=100, height=28)

# Scene 1 — Introduction
gen.wait(1.0)
gen.clear_screen()
gen.wait(1.0)
gen.output_line("\x1b[1;36mDecisionDrift\x1b[0m")
gen.output_line("AI-powered Decision Governance", 1.0)
gen.output_line("")
gen.output_line("Repository \x1b[1;33m→\x1b[0m Decisions \x1b[1;33m→\x1b[0m Rules \x1b[1;33m→\x1b[0m Enforcement", 2.0)
gen.wait(2.0)

gen.clear_screen()
gen.add_event("o", PROMPT)
gen.wait(1.0)

# Scene 2 — Navigate to Project
gen.add_event("o", "\r")
gen.type_command(PROMPT, "cd sample-fastapi-project")
gen.wait(0.5)

gen.type_command(PROMPT_PROJ, "tree")
tree_output = """\x1b[1;34msample-fastapi-project\x1b[0m
├── \x1b[1;34mapp\x1b[0m
├── \x1b[1;34mapi\x1b[0m
├── \x1b[1;34mmodels\x1b[0m
├── \x1b[1;34mauth\x1b[0m
├── \x1b[1;34mmigrations\x1b[0m
├── Dockerfile
├── requirements.txt
├── docker-compose.yml
└── README.md"""
for line in tree_output.split('\n'):
    gen.output_line(line, 0.04)
gen.wait(2.0)
gen.output_line("")

# Scene 3 — Bootstrap
gen.type_command(PROMPT_PROJ, "decisiondrift bootstrap .")
gen.wait(0.5)
gen.output_line("Scanning repository...", 1.5)
gen.output_line("")

checks = [
    "FastAPI detected",
    "SQLAlchemy detected",
    "Alembic detected",
    "JWT Authentication detected",
    "Docker detected",
    "Redis detected",
    "Celery detected",
    "RBAC detected",
    "Blueprints / Routers detected"
]
for check in checks:
    gen.output_line(f"\x1b[1;32m✓\x1b[0m {check}", 0.3)

gen.wait(1.0)
gen.output_line("")
gen.output_line("Analyzing architectural patterns...", 1.5)
gen.output_line("Finding design decisions...", 1.5)
gen.output_line("Removing duplicates...", 1.0)
gen.output_line("")
gen.output_line("\x1b[1;32mDone.\x1b[0m", 2.0)

# Scene 4 — Generated ADRs
gen.clear_screen()
gen.wait(1.0)
gen.output_line("\x1b[1mGenerated 7 candidate ADRs\x1b[0m\n", 1.0)

adrs = [
    ("[1]", "Use FastAPI as the backend framework", "98%"),
    ("[2]", "Database migrations managed with Alembic", "95%"),
    ("[3]", "JWT authentication for stateless auth", "96%"),
    ("[4]", "Containerized deployment using Docker", "94%")
]

for idx, title, conf in adrs:
    gen.output_line(f"\x1b[1;34m{idx}\x1b[0m")
    gen.output_line(f"{title}")
    gen.output_line("")
    gen.output_line(f"Confidence: \x1b[1;32m{conf}\x1b[0m")
    gen.output_line("\x1b[2m----------------------------\x1b[0m")
    gen.wait(1.5)

gen.output_line("...", 2.0)
gen.wait(1.0)
gen.clear_screen()

# Scene 5 — List Decisions
gen.type_command(PROMPT_PROJ, "decisiondrift adr list")
list_output = """\x1b[1mID       Status      Title\x1b[0m
ADR-001  \x1b[33mProposed\x1b[0m    FastAPI Framework
ADR-002  \x1b[33mProposed\x1b[0m    Alembic Migrations
ADR-003  \x1b[33mProposed\x1b[0m    JWT Authentication
ADR-004  \x1b[33mProposed\x1b[0m    Docker Deployment
ADR-005  \x1b[33mProposed\x1b[0m    Redis Caching
ADR-006  \x1b[33mProposed\x1b[0m    Celery Background Tasks
ADR-007  \x1b[33mProposed\x1b[0m    RBAC Authorization"""
for line in list_output.split('\n'):
    gen.output_line(line, 0.05)
gen.wait(2.5)
gen.output_line("")

# Scene 6 — Review One ADR
gen.type_command(PROMPT_PROJ, "decisiondrift adr show ADR-003")
adr_output = """\x1b[1mADR-003\x1b[0m

\x1b[1;34mTitle\x1b[0m
Use JWT Authentication

\x1b[1;34mStatus\x1b[0m
\x1b[33mProposed\x1b[0m

\x1b[1;34mContext\x1b[0m
The project exposes REST APIs requiring stateless authentication.

\x1b[1;34mDecision\x1b[0m
Use JWT tokens for authentication.

\x1b[1;34mConsequences\x1b[0m
\x1b[1;32m✓\x1b[0m Scalable
\x1b[1;32m✓\x1b[0m Stateless
\x1b[1;32m✓\x1b[0m Easy API integration

\x1b[1;34mConfidence\x1b[0m
\x1b[1;32m96%\x1b[0m"""
for line in adr_output.split('\n'):
    gen.output_line(line, 0.05)
gen.wait(3.5)
gen.output_line("")

# Scene 7 — Approve Decision
gen.type_command(PROMPT_PROJ, "decisiondrift adr approve ADR-003")
gen.wait(0.5)
gen.output_line("\x1b[1;32m✓ ADR approved.\x1b[0m\n", 1.0)
gen.output_line("Status changed:")
gen.output_line("")
gen.output_line("\x1b[33mProposed\x1b[0m", 0.5)
gen.output_line("↓", 0.5)
gen.output_line("\x1b[1;32mApproved\x1b[0m", 1.5)
gen.wait(1.5)
gen.output_line("")

# Scene 8 — List Again
gen.type_command(PROMPT_PROJ, "decisiondrift adr list")
list_output_2 = """\x1b[1mID       Status      Title\x1b[0m
ADR-001  \x1b[33mProposed\x1b[0m    FastAPI Framework
ADR-002  \x1b[33mProposed\x1b[0m    Alembic Migrations
ADR-003  \x1b[1;32mApproved\x1b[0m    JWT Authentication
ADR-004  \x1b[33mProposed\x1b[0m    Docker Deployment
ADR-005  \x1b[33mProposed\x1b[0m    Redis Caching
ADR-006  \x1b[33mProposed\x1b[0m    Celery Background Tasks
ADR-007  \x1b[33mProposed\x1b[0m    RBAC Authorization"""
for line in list_output_2.split('\n'):
    gen.output_line(line, 0.05)
gen.wait(3.5)

# Scene 9 — Governance Vision
gen.clear_screen()
gen.wait(1.0)

gen.output_line("\x1b[1mCurrent\x1b[0m", 1.0)
gen.output_line("")
gen.output_line("Repository", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("Detected Decisions", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("Approved Decisions", 2.0)

gen.output_line("")
gen.output_line("\x1b[1;36mFuture\x1b[0m", 1.0)
gen.output_line("")
gen.output_line("Repository", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("Decisions", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("Rules", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("Policy Enforcement", 0.4)
gen.output_line("↓", 0.4)
gen.output_line("\x1b[1;31mDecision Drift Detection\x1b[0m", 3.0)

# Scene 10 — Closing
gen.clear_screen()
gen.wait(1.0)

gen.output_line("\x1b[1;36mDecisionDrift\x1b[0m", 1.0)
gen.output_line("")
gen.output_line("Understand architecture.", 1.0)
gen.output_line("Document decisions.", 1.0)
gen.output_line("Govern engineering.", 1.0)
gen.output_line("")
gen.output_line("\x1b[3mOne command away.\x1b[0m", 2.0)
gen.output_line("")

gen.type_command(PROMPT, "decisiondrift --help")

help_output = """\x1b[1mUsage: decisiondrift [OPTIONS] COMMAND [ARGS]...\x1b[0m

  AI-powered decision governance.

\x1b[1mOptions:\x1b[0m
  --version  Show the version and exit.
  --help     Show this message and exit.

\x1b[1mCommands:\x1b[0m
  bootstrap  Bootstrap ADRs from an existing repository.
  adr        Manage Architecture Decision Records.
  audit      Audit the repository for decision drift."""
for line in help_output.split('\n'):
    gen.output_line(line, 0.05)
gen.wait(2.0)

gen.output_line("")
gen.output_line("\x1b[1;34mhttps://github.com/madhan-karthikeyan/DecisionDrift\x1b[0m", 1.0)
gen.output_line("")
gen.output_line("\x1b[1;33m⭐ Star the project\x1b[0m", 3.0)

gen.save()
print("Saved decisiondrift_demo.cast")
