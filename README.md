<div align="center">

<!-- https://coolors.co/gradient-palette/f72585-066da5?number=3 -->

[![GitHub stars](https://img.shields.io/github/stars/msr8/tagsafe?color=F72585&labelColor=302D41&style=for-the-badge)](https://github.com/msr8/tagsafe/stargazers)
[![GitHub last commit](https://img.shields.io/github/last-commit/msr8/tagsafe?color=7F4995&labelColor=302D41&style=for-the-badge)](https://github.com/msr8/tagsafe/commits/main)
[![GitHub issues](https://img.shields.io/github/issues/msr8/tagsafe?color=066DA5&labelColor=302D41&style=for-the-badge)](https://github.com/msr8/tagsafe/issues)

<br>

<h1>TagSafe</h1>
<p><em>Automated security scanning, natively integrated into your GitHub workflow</em></p>

</div>

<br>

# Index
1. [Abstract](#abstract)
   - [Features](#features)
   - [Tech Stack](#tech-stack)
   - [Supported Scanners](#supported-scanners)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Usage](#usage)
   <!-- - [Running via Docker](#running-via-docker) -->
   - [Running via Source](#running-via-source)
5. [GitHub App Setup](#github-app-setup)
6. [Environment Variables](#environment-variables)
7. [Endpoints](#endpoints)



<br><br>



# Abstract

**Problem Statement:** Modern software development pipelines lack integrated, real-time static analysis security testing (SAST) at the repository level. Developers often discover vulnerabilities only after code has already been merged, making remediation costly and time-consuming. Existing tools are fragmented, requiring manual invocation and expert knowledge to interpret results

**Purpose and Contribution:** TagSafe is a self-hosted, GitHub-native automated security scanning platform that hooks directly into repository events — commits and pull requests — to automatically scan code using multiple industry-standard SAST tools. It provides unified findings via a dashboard, inline PR comments with LLM-generated summaries, and configurable email alerts, all without changing the developer's existing workflow

**Methods and Approach:** TagSafe runs as a Flask application that registers a GitHub App to receive webhook events. On each push or pull request, it clones the repository (or downloads changed files for PRs), detects the languages present, and dispatches the appropriate scanners. Results are normalised, persisted in SQLite via SQLAlchemy, and surfaced through a glassmorphic web dashboard. A locally-hosted LLM (Phi-3 via Ollama) optionally synthesises findings into a concise PR comment

<br>

### Features

1. **GitHub-Native Integration:** registers as a GitHub App; receives push and PR webhooks automatically
2. **Multi-Language SAST:** orchestrates 10+ scanners across Python, Go, JavaScript, C/C++, Ruby, Rust, and more
3. **LLM-Powered Summaries:** uses a locally-hosted Phi-3 model to generate human-readable security summaries posted as PR comments
4. **Unified Dashboard:** glassmorphic web UI showing findings per-repo, per-commit, and per-PR with severity colour coding
5. **Email Alerting:** configurable per-user severity threshold; sends HTML email reports with AI summary and findings table
6. **Secret Detection:** Gitleaks and Trivy scan for hardcoded secrets and credentials across every push
7. **Malware Signatures:** YARA rules scan for known malicious code patterns
8. **Fully Self-Hosted:** No data leaves your infrastructure; LLM runs locally via Ollama

<br>

### Tech Stack

1. **Backend & Framework**
   - **Python (Flask):** Core web framework and webhook handler
   - **Flask-Dance:** GitHub OAuth 2.0 authentication
   - **Flask-SQLAlchemy + SQLite:** ORM and database for findings, commits, PRs, and users
   - **Flask-Session:** Server-side session management
   - **GitPython:** Clones repositories for full-commit scanning
2. **Security Scanners**
   - Language-specific and general-purpose SAST tools (see [Supported Scanners](#supported-scanners))
3. **AI / LLM**
   - **Ollama (Phi-3):** Local LLM for generating findings summaries; no external API calls
4. **Infrastructure**
   - **Docker + Docker Compose:** Containerised deployment of the Flask app and Ollama service
5. **Frontend**
   - **HTML5 / CSS3 / JavaScript:** Custom glassmorphic dashboard
   - **Lucide Icons + Toastify + PrismJS:** UI libraries for icons, notifications, and code highlighting

<br>

### Supported Scanners

| Scanner | Language / Target | What It Finds |
|---|---|---|
| **Bandit** | Python | Insecure function calls, crypto issues, injections |
| **Semgrep** | Multi-language | Custom rules, OWASP patterns, CVE-mapped findings |
| **Gosec** | Go | Hardcoded credentials, unsafe packages, SQL injection |
| **NodeJSScan** | JavaScript / Node.js | XSS, SSRF, command injection, prototype pollution |
| **Cppcheck** | C / C++ | Memory errors, undefined behaviour, style issues |
| **Brakeman** | Ruby / Rails | SQL injection, XSS, mass assignment, CSRF |
| **cargo-audit** | Rust (Cargo.lock) | Known CVEs in Rust dependencies |
| **Trivy** | All (FS scan) | Vulnerable packages, misconfigurations, secrets |
| **Gitleaks** | All | Hardcoded secrets, API keys, tokens |
| **YARA** | All | Malware signatures, known malicious code patterns |
| **OWASP Dependency-Check** | All (manifest files) | CVEs in third-party dependencies |



<br><br>



# System Architecture

The platform is divided into five layers:

![System Architecture Diagram](diagrams/sys%20architecture.svg)



<br><br>



# Database Schema

The database consists of five tables with the following relationships:

- A **User** has many **Installations**
- An **Installation** has many **Commits** and **Pull Requests**
- A **Commit** has many **Findings**
- A **Pull Request** has many **Findings**

![ER Diagram](diagrams/ER.svg)



<br><br>



# Usage

### Running via Docker

<!-- **Pre-requisites:** [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) must be installed and running. You will also need a GitHub App configured (see [GitHub App Setup](#github-app-setup)).

```bash
# Clone the repository
git clone https://github.com/msr8/tagsafe
cd tagsafe/src

# Create your .env file (see Environment Variables section)
cp .env.example .env
# Edit .env with your credentials

# Build and start both the web app and Ollama
docker compose up --build
```

The application will be available at `http://localhost:5000`. On first start, Docker Compose will automatically pull the Phi-3 model into the Ollama container (this may take a few minutes depending on your connection).

> [!NOTE]
> The Ollama container requires ~2 GB of disk space for the Phi-3 model. If you do not need LLM summaries, set `LLM_ENABLED=False` in your `.env` file and remove the `ollama` service from `docker-compose.yml` to save resources

<br> -->

### Running via Source

**Pre-requisites:** Python 3.10+, Go, Ruby, Rust (`cargo`), Ollama, and the scanner CLIs listed in [src/app/scanners/commands.txt](src/app/scanners/commands.txt) must be installed on your system

```bash
# Clone the repository
git clone https://github.com/msr8/tagsafe
cd tagsafe/src

# Install Python dependencies
pip install -r requirements.txt

# Install Python-based scanners
pip install bandit semgrep njsscan guarddog safety

# Clone YARA rules
git clone https://github.com/Yara-Rules/rules.git app/scanners/yara_rules

# Set up your .env file, then run
flask run
```

Also you need to have Ollama installed and the Phi-3 model pulled locally:

```bash
ollama pull phi3
ollama run --model phi3 --host
```

The application will be accessible at `http://127.0.0.1:5000`

> [!WARNING]
> These instructions are intended for local/development use only. For production, use a WSGI server such as [Gunicorn](https://gunicorn.org/) behind a reverse proxy like [Nginx](https://www.nginx.com/), and set `OAUTHLIB_INSECURE_TRANSPORT=0`



<br><br>



# GitHub App Setup

TagSafe works by registering a GitHub App that sends webhooks to your running instance. Follow these steps:

1. Go to **GitHub → Settings → Developer Settings → GitHub Apps** and click **New GitHub App**
2. Set the **Webhook URL** to `https://<your-domain>/webhook` (use [ngrok](https://ngrok.com/) for local development)
3. Generate a **Private Key** and save it as `github-private-key<date>.pem` in the `src/` directory. Update `GITHUB_KEY_PATH` in `consts.py` accordingly
4. Under **Permissions**, enable:
   - Repository → Contents: **Read**
   - Pull Requests → **Read & Write** (to post comments)
5. Subscribe to **push** and **pull_request** events
6. After creating the app, note the **App ID** (this is your `GITHUB_CLIENT_ID`) and generate a **Client Secret**
7. Install the app on your repositories via `https://github.com/apps/<your-app-name>/installations/new`



<br><br>



# Environment Variables

Create a `.env` file in the `src/` directory with the following variables:

```env
# GitHub App credentials
GITHUB_CLIENT_ID=<your-github-app-id>
GITHUB_CLIENT_SECRET=<your-github-app-client-secret>
GITHUB_APP_NAME=<your-github-app-name>

# Email alerting (Gmail)
MY_EMAIL=youremail@gmail.com
GMAIL_APP_PASSWORD=<your-gmail-app-password>

# LLM configuration
LLM_ENABLED=True
LLM_MODEL=phi3
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
```

To get the gmail app password, follow these steps:

1. Go to your Google Account settings
2. Navigate to the "Security" tab
3. Under "Signing in to Google," select "App Passwords"
4. You may need to verify your identity by entering your password or using 2FA
5. In the "Select app" dropdown, choose "Other (Custom name)"
6. Enter a name (eg, "TagSafe") and click "Generate"
7. A 16-character app password will be displayed. Copy this password and use it as the value for `GMAIL_APP_PASSWORD` in your `.env` file

<br><br>



# Endpoints

| URL Path | Method | Description |
|---|---|---|
| `/` | `GET` | Landing page |
| `/dashboard` | `GET` | Main dashboard — repos, commits, PR findings |
| `/webhook` | `POST` | GitHub App webhook receiver |
| `/api/change-config` | `POST` | Update notification email and severity threshold |
| `/api/reload-repos` | `POST` | Refresh the list of authorised repositories |
| `/login/github` | `GET` | Initiates GitHub OAuth login |
| `/github-authorised/` | `GET` | GitHub OAuth callback |
| `/logout/` | `GET` | Logs the user out |
| `/session` | `GET` | Debug — inspect current session (dev only) |