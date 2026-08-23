#!/usr/bin/env bash
# scripts/bootstrap_vm.sh
#
# One-shot bootstrap script for the Azure VM (Ubuntu 24.04 LTS, x86_64).
# Installs: Docker CE, kubectl, kind, Helm 3, Java 21, tla2tools.jar.
#
# Usage (run as non-root user with sudo):
#   chmod +x scripts/bootstrap_vm.sh
#   ./scripts/bootstrap_vm.sh
#
# After completion, verify:
#   docker version
#   kubectl version --client
#   kind version
#   helm version
#   java -jar ~/tla/tla2tools.jar -help | head -1

set -euo pipefail

LOG() { printf '\033[1;34m[bootstrap]\033[0m %s\n' "$*"; }
WARN() { printf '\033[1;33m[bootstrap][WARN]\033[0m %s\n' "$*" >&2; }
DIE() { printf '\033[1;31m[bootstrap][FATAL]\033[0m %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -ne 0 ]] || DIE "do not run as root"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
LOG "installing system packages (apt)"
sudo apt update -y
sudo apt install -y ca-certificates curl gnupg lsb-release default-jre-headless

# ---------------------------------------------------------------------------
# 2. Docker CE
# ---------------------------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  LOG "installing Docker CE"
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt update -y
  sudo apt install -y docker-ce docker-ce-cli containerd.io
  sudo usermod -aG docker "$USER"
  WARN "you must log out and back in for docker group to take effect"
else
  LOG "Docker CE already installed"
fi

# ---------------------------------------------------------------------------
# 3. kubectl
# ---------------------------------------------------------------------------
if ! command -v kubectl >/dev/null 2>&1; then
  LOG "installing kubectl"
  KUBECTL_VERSION="$(curl -L -s https://dl.k8s.io/release/stable.txt)"
  curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" | \
    sudo tee /usr/local/bin/kubectl > /dev/null
  sudo chmod +x /usr/local/bin/kubectl
else
  LOG "kubectl already installed: $(kubectl version --client --short 2>/dev/null || echo 'unknown')"
fi

# ---------------------------------------------------------------------------
# 4. kind
# ---------------------------------------------------------------------------
if ! command -v kind >/dev/null 2>&1; then
  LOG "installing kind"
  sudo curl -fsSL "https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64" \
    -o /usr/local/bin/kind
  sudo chmod +x /usr/local/bin/kind
else
  LOG "kind already installed: $(kind version)"
fi

# ---------------------------------------------------------------------------
# 5. Helm 3
# ---------------------------------------------------------------------------
if ! command -v helm >/dev/null 2>&1; then
  LOG "installing Helm 3"
  curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | \
    sudo bash
else
  LOG "Helm already installed: $(helm version --short)"
fi

# ---------------------------------------------------------------------------
# 6. Java + TLA+ tools (for Day-10 TLC verification)
# ---------------------------------------------------------------------------
LOG "verifying Java"
java -version

if [[ ! -f "$HOME/tla/tla2tools.jar" ]]; then
  LOG "downloading tla2tools.jar v1.8.0"
  mkdir -p "$HOME/tla"
  curl -L -o "$HOME/tla/tla2tools.jar" \
    https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar
fi

LOG "alias 'tlc' added to ~/.bashrc (effective on next login)"
grep -qxF 'alias tlc="java -jar ~/tla/tla2tools.jar"' "$HOME/.bashrc" || \
  echo 'alias tlc="java -jar ~/tla/tla2tools.jar"' >> "$HOME/.bashrc"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
LOG "bootstrap complete"
cat <<EOF
Next steps:
  1. Log out and back in (for docker group membership)
  2. cd ~/k8-auto-scaling-self-healing
  3. ./scripts/build_image.sh
  4. ./scripts/deploy_infra.sh
  5. ./scripts/run_pipeline.sh
EOF