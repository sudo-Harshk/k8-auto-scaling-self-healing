#!/bin/bash
# bootstrap.sh — One-command installer for SHIELD-AI on a clean Ubuntu 24.04
# (or any Debian-family Linux) system. Designed for students running the demo
# inside WSL2 on a 16 GB Windows laptop.
#
# Target environment:
#   - Ubuntu 24.04 LTS (cloud VM, WSL2, native Linux, VirtualBox Ubuntu guest)
#   - 8 GB RAM minimum; 16 GB recommended for the full 12-step demo
#   - User with sudo rights; outbound HTTPS to raw.githubusercontent.com,
#     github.com, dl.k8s.io, kind.sigs.k8s.io, download.docker.com
#
# What this script does:
#   [1] installs Docker Engine (NOT Docker Desktop - no license, no GUI)
#   [2] installs OpenJDK 17       (for the TLA+ TLC model-checker)
#   [3] installs kubectl 1.30     (Kubernetes CLI)
#   [4] installs kind 0.23        (local K8s in Docker)
#   [5] installs Helm 3          (Kubernetes package manager)
#   [6] clones the SHIELD-AI repo, pre-builds the Python image, adds demo
#       aliases to ~/.bashrc
#
# Usage:
#   bash bootstrap.sh
#   curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
#
# Idempotency:
#   - apt packages skip if already installed (via dpkg-query)
#   - kubectl / kind / helm binaries skip if already on PATH
#   - git clone skips if the repo already exists (runs git pull instead)
#
# Author: sudo-Harshk <[YOUR_EMAIL]>
# License: repository LICENSE

set -euo pipefail

REPO_URL="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing.git"
REPO_BRANCH="main"
INSTALL_DIR="$HOME/k8-auto-scaling-self-healing"

# ----- helper -----
have() { command -v "$1" >/dev/null 2>&1; }
apt_installed() { dpkg-query -W -f='${Status}' "$1" 2>/dev/null | grep -q "install ok installed"; }

step() { echo; echo "==> $1"; }
ok()   { echo "    [ok] $1"; }
skip() { echo "    [skip] $1"; }
warn() { echo "    [warn] $1"; }

step "Pre-flight"
if ! have sudo; then
  echo "ERROR: sudo not found. Re-run as a sudo-capable user." >&2
  exit 1
fi
if ! have apt-get; then
  echo "ERROR: apt-get not found. This script targets Debian-family (Ubuntu 24.04)." >&2
  exit 1
fi
ARCH="$(uname -m)"
case "$ARCH" in
  amd64|x86_64) BIN_ARCH=amd64 ;;
  arm64|aarch64) BIN_ARCH=arm64 ;;
  *) echo "ERROR: unsupported architecture $ARCH" >&2; exit 1 ;;
esac
ok "arch=$ARCH, sudo ok, apt ok"

# ----- [1/6] Docker Engine -----
step "[1/6] Docker Engine"
if have docker; then
  skip "docker already installed: $(docker --version)"
else
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  # shellcheck disable=SC1091
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  ok "docker installed: $(docker --version)"
fi
if id -nG "$USER" | grep -qw docker; then
  skip "user $USER already in docker group"
else
  sudo usermod -aG docker "$USER"
  warn "added $USER to docker group; new groups activate after next shell.  Docker commands will work in any *new* terminal session opened after this script finishes, or after running:  newgrp docker"
fi

# Make docker daemon persistent on WSL (and start it in the current shell)
if grep -qi microsoft /proc/version; then
  if [ ! -f /etc/wsl.conf ]; then
    sudo tee /etc/wsl.conf > /dev/null <<'EOF'
# SHIELD-AI: keep docker daemon alive across WSL reboots
[boot]
systemd=true
EOF
    ok "wrote /etc/wsl.conf [boot] systemd=true (run 'wsl --shutdown' after this to activate)"
  else
    skip "/etc/wsl.conf already exists"
  fi
  if have systemctl; then
    if ! systemctl is-active --quiet docker 2>/dev/null; then
      sudo systemctl enable docker 2>/dev/null || true
      sudo systemctl start docker || sudo service docker start
      ok "docker daemon started"
    else
      skip "docker daemon already active"
    fi
  else
    sudo service docker start || true
    ok "docker daemon start attempted (service command)"
  fi
fi

# ----- [2/6] OpenJDK 17 -----
step "[2/6] OpenJDK 17 (for TLA+ TLC)"
if apt_installed openjdk-17-jdk-headless; then
  skip "openjdk-17-jdk-headless already installed"
else
  sudo apt-get install -y openjdk-17-jdk-headless
  ok "openjdk-17 installed: $(java -version 2>&1 | head -1)"
fi

# ----- [3/6] kubectl -----
step "[3/6] kubectl 1.30"
if have kubectl; then
  skip "kubectl already installed: $(kubectl version --client --output=yaml 2>/dev/null | grep gitVersion || kubectl version --client=true --short)"
else
  curl -fsSLO "https://dl.k8s.io/release/v1.30.0/bin/linux/$BIN_ARCH/kubectl"
  sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
  rm -f kubectl
  ok "kubectl installed: $(kubectl version --client --short)"
fi

# ----- [4/6] kind -----
step "[4/6] kind 0.23"
if have kind; then
  skip "kind already installed: $(kind version)"
else
  curl -fsSLO "https://kind.sigs.k8s.io/dl/v0.23.0/kind-linux-$BIN_ARCH"
  sudo install -o root -g root -m 0755 "kind-linux-$BIN_ARCH" /usr/local/bin/kind
  rm -f "kind-linux-$BIN_ARCH"
  ok "kind installed: $(kind version)"
fi

# ----- [5/6] Helm -----
step "[5/6] Helm 3"
if have helm; then
  skip "helm already installed: $(helm version --short)"
else
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ok "helm installed: $(helm version --short)"
fi

# ----- [6/6] Clone repo + pre-build image + aliases -----
step "[6/6] Clone SHIELD-AI repo, pre-build image, add aliases"
if [ -d "$INSTALL_DIR/.git" ]; then
  skip "$INSTALL_DIR already exists - running git pull"
  git -C "$INSTALL_DIR" pull --ff-only "$REPO_URL" "$REPO_BRANCH" || warn "git pull failed (offline?); existing repo retained"
else
  git clone --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
  ok "cloned to $INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Pre-build k8-ai-ops:dev image (saves 5 min per demo)
if docker image inspect k8-ai-ops:dev >/dev/null 2>&1; then
  skip "k8-ai-ops:dev image already present"
else
  warn "pre-building k8-ai-ops:dev (one-time, ~5 min). Run this only once."
  make build-image
  ok "k8-ai-ops:dev image built"
fi

# Aliases (don't clobber)
ALIASES_BLOCK='
# ---- SHIELD-AI demo aliases (added by bootstrap.sh) ----
alias demo='"'"'cd ~/k8-auto-scaling-self-healing && make demo'"'"'
alias demo-quick='"'"'cd ~/k8-auto-scaling-self-healing && bash scripts/demo/quick.sh'"'"'
alias demo-reset='"'"'cd ~/k8-auto-scaling-self-healing && make reset && make bootstrap'"'"'
alias demo-help='"'"'cat ~/k8-auto-scaling-self-healing/RUN_DEMO.md'"'"'
alias tlac='"'"'cd ~/k8-auto-scaling-self-healing && make tla-composition'"'"'
alias paper='"'"'cd ~/k8-auto-scaling-self-healing && make paper && xdg-open docs/paper/main.pdf'"'"'
'

if grep -q "SHIELD-AI demo aliases" "$HOME/.bashrc" 2>/dev/null; then
  skip "SHIELD-AI aliases already present in ~/.bashrc"
else
  printf '%s\n' "$ALIASES_BLOCK" >> "$HOME/.bashrc"
  ok "appended SHIELD-AI aliases to ~/.bashrc"
fi

step "Bootstrap complete!"
echo
echo "  Total time: depends on network (typically 10-20 min on a 50 Mbps link)"
echo "  WSL2 users:  open a NEW terminal to pick up docker group membership,"
echo "              then run  wsl --shutdown  (once) so systemd starts docker on next boot."
echo
echo "  Daily demo commands:"
echo "    demo-help     print this cheat-sheet  $(type demo-help >/dev/null 2>&1 || echo '(re-run: source ~/.bashrc)')"
echo "    demo-quick    2-min highlight run (TLC traces + paper + audit logs + stats)"
echo "    demo          full 30-min 12-step live demo on a kind cluster"
echo "    demo-reset    wipe kind cluster + rebuild from scratch"
echo "    tlac          just the TLA+ composition theorem (4 min)"
echo "    paper         build + open the IEEE paper PDF"
echo
echo "  Verify the install:"
echo "    docker run hello-world       # docker daemon + group membership"
echo "    kubectl version --client     # 1.30.x"
echo "    kind version                 # 0.23.x"
echo "    helm version                 # 3.x"
echo "    java -version                # 17.x"
echo "    tla2sany --version           # should print 'Version 2.2 of 2026.08.21' or similar"
echo "    cd ~/k8-auto-scaling-self-healing && python3 scripts/_phase5_audit.py"
echo "        expect: SOURCED=56, UNSOURCED=0"
echo
echo "  Open a fresh terminal now, then type:  demo-help"
echo
