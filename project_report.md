# Project Overview: Automated Repository Security Dashboard

## Executive Summary
This project is a comprehensive automated security scanning and monitoring platform designed to seamlessly integrate with GitHub repositories. Built on the Flask web framework, the application functions as a dynamic, continuous security evaluator. By tapping into GitHub webhooks, it acts as an intermediary pipeline that automatically scans source code for vulnerabilities upon every Commit push and Pull Request synchronization.

## System Architecture & Core Workflows

The application is built using a modular micro-architecture within Flask, organized into Blueprints for routing, a centralized service layer, and a dedicated scanner orchestration engine.

### 1. Webhook Engine & Event Processing
The core engine relies on a robust webhook listener (`app/routes/webhook.py`) that subscribes to GitHub app events:
- **Installation Lifecycle:** Tracks when the GitHub App is installed, suspended, unsuspended, or deleted by a user, dynamically updating the database to mirror permissions.
- **Repository Management:** Automatically tracks additions or removals of repositories granted to the GitHub App.
- **Commit (Push) Scanning:** When code is pushed, the engine retrieves a lightweight installation token, fetches the list of commits, and filters out previously scanned commits. It then clones the repository precisely at the latest commit SHA into a temporary directory for deep scanning.
- **Pull Request Scanning:** For PRs, the engine is optimized to avoid full repository clones. Instead, it interacts with the GitHub API to fetch only the changed files. It downloads raw file contents into a temporary staging area to selectively run scanners, drastically reducing network overhead and scanning time.

### 2. Scanner Orchestration
The scanning layer (`app/scanners/__init__.py`) intelligently determines which Static Application Security Testing (SAST) tools to invoke based on file extensions. Supported analyzers include:
- **`py_bandit`**: Analyzes Python (`.py`) files for common security issues.
- **`go_gosec`**: Inspects Go (`.go`) source code for security flaws.
- **`js_nodejsscan`**: Targets Node.js/JavaScript (`.js`) code for vulnerabilities.
- **`c_cppcheck`**: Scans C/C++ (`.c`, `.cpp`, `.h`, `.hpp`) implementations.
- **`all_semgrep`**: Acts as a universal, multi-language semantic grep tool.

The orchestration layer aggregates findings across these disparate tools, standardizes them into a unified format, and associates them with the parent Commit or PR before persistence.

### 3. Automated Code Review (LLM Integration)
To provide actionable intelligence rather than raw scanner output, the platform utilizes local AI through Ollama (`app/services/__init__.py`). 
When vulnerabilities exceed the user's defined severity threshold, the system passes the serialized findings to the LLM. The AI generates a contextualized, human-readable summary that explains the security implications.
- **PR Comments:** For Pull Requests, the AI-generated summary, along with a detailed Markdown table of findings, is automatically posted back to GitHub as a PR comment.

### 4. Alerting & Notification System
The application features a granular notification engine utilizing `smtplib` over modern SSL.
- **Customized Thresholds:** Users can specify customized severity thresholds in their preferences (e.g., only trigger emails on `HIGH` or `CRITICAL` findings).
- **Rich HTML Emails:** The alerting system sends beautifully formatted HTML emails containing the AI-generated vulnerability summary, providing developers immediate context directly in their inbox without needing to access the dashboard.

## Technical Architecture & Database Design

The application utilizes a PostgreSQL-compatible relational database via SQLAlchemy (`app/models.py`), mapped across the following interconnected models:

* **Users (`users`):** Stores authentication details natively seeded via Flask-Dance GitHub OAuth integration. It also stores customized user preferences mapped as JSON attributes.
* **Installations (`installations`):** Tracks the relationship between a user and their GitHub App installation footprint, storing JSON arrays of accessible repositories and their active billing/suspension state.
* **Commits (`commits`) & Pull Requests (`pull_requests`):** Core code-change entities establishing the timeline of the codebase. They track critical metadata like timestamps, author tracking, and the scanning-state lifecycle (`to_scan`, `fully_scanned`).
* **Findings (`findings`):** The central entity representing a discrete vulnerability. Findings maintain a foreign-key relationship with their parent Commit or PR and encapsulate:
  - The analysis `tool` used.
  - The assigned `severity` & `confidence`.
  - Specific `file_path`, `line_start`, and `line_end`.
  - Relevant industry standards bindings (`CWE`, `OWASP`).
  - Code snippets and the scanner's descriptive message.

## Development Roadmap & Status

**Currently Implemented:**
* Complete GitHub OAuth flow via `make_github_blueprint`.
* Functional webhook handler processing Pings, Installation events, Commits, and PRs.
* Relational database tracking across 5 robust models.
* Dynamic scanner invocation mapped to file extensions.
* Full local LLM analysis pipeline powered by Ollama.
* SMTP-based email notification system.
* Dashboard UI utilizing `base.css` and `main.js`.

**Upcoming Objectives (TODO):**
* Integration of additional specialized security scanners to expand language coverage.
* Performance optimizations to reduce GitHub API token consumption, potentially utilizing better caching or GraphQL.
* UX improvements including a dedicated "Reload Repositories" button to manually synchronize state.
* Implementing strict API limits and header distribution for scalable hosting.
