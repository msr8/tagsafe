FROM ubuntu:22.04

# Prevent prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.cargo/bin:/root/go/bin:/usr/local/go/bin:$PATH"

# Point to Indian mirrors for much faster apt-get update speeds
RUN sed -i 's/archive.ubuntu.com/in.archive.ubuntu.com/g' /etc/apt/sources.list

# # Install system dependencies (Python, Go, Ruby, curl, git, unzip, Cppcheck, Yara, Java)
# RUN apt-get update && apt-get install -y \
#     python3 python3-pip python3-venv \
#     golang-go \
#     ruby ruby-dev \
#     curl git unzip \
#     cppcheck yara \
#     default-jre \
#     && rm -rf /var/lib/apt/lists/*

# Install system dependencies (Python, Go, Ruby, curl, git, unzip, Cppcheck, Yara, Java)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    golang-go \
    ruby ruby-dev \
    curl git unzip \
    cppcheck yara \
    default-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Install Rust and Cargo
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Setup workspace
WORKDIR /app

# Install CLI Scanners
# 1. Gosec
RUN curl -sfL https://raw.githubusercontent.com/securego/gosec/master/install.sh | sh -s -- -b /usr/local/bin
# 2. Gitleaks
RUN go install github.com/zricethezav/gitleaks/v8@latest
# 3. Brakeman
RUN gem install brakeman
# 4. CargoAudit
RUN cargo install cargo-audit
# 5. Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
# 6. OWASP Dependency-Check (Needs Java)
RUN curl -L -o dependency-check.zip https://github.com/jeremylong/DependencyCheck/releases/download/v9.0.9/dependency-check-9.0.9-release.zip && \
    unzip dependency-check.zip -d /usr/share/ && \
    ln -s /usr/share/dependency-check/bin/dependency-check.sh /usr/local/bin/dependency-check.sh && \
    rm dependency-check.zip

# Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Python-based Scanners
RUN pip3 install --no-cache-dir bandit semgrep njsscan guarddog safety

# Setup Yara Rules inside the required directory
RUN mkdir -p /app/app/scanners && \
    git clone https://github.com/Yara-Rules/rules.git /app/app/scanners/yara_rules

# Copy source code into /app
COPY . .

# Run the Flask app
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
# The OLLAMA_HOST will be overwritten by docker-compose environment variable if needed
ENV OLLAMA_HOST="ollama" 

EXPOSE 5000
CMD ["flask", "run"]
