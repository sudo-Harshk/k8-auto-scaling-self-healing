# RECIPIENT SETUP GUIDE — Windows 11 to Working Project

> **Read this once. Then follow each step in order.**
> **Assume nothing is installed. Start from zero.**

This guide takes you from a fresh Windows 11 machine (no WSL, no Docker, no
nothing) to a fully working SHIELD-AI project. Each step shows:
- **What you do** (the exact command)
- **What happens** (what the command does)
- **What you see** (example output)
- **What to check** (success criteria)

If any step fails, go to the **TROUBLESHOOTING** section at the end.

---

## BEFORE YOU START

You need:
- Windows 11 (any edition, Home or Pro)
- Administrator access to your machine
- 16 GB RAM minimum (8 GB works but is slow)
- 20 GB free disk space
- Internet connection (for the first 20 minutes; not needed for the demo)
- A user account with a non-empty password (Windows requires this for WSL2)

**Estimated total time:** 30-45 minutes
- Steps 1-3 (Windows setup): 10-15 min
- Steps 4-5 (Ubuntu setup): 5 min
- Step 6 (project install): 15-20 min
- Steps 7-8 (verify): 5 min

---

## STEP 1: Open PowerShell as Administrator

**What you do:**
1. Click the Windows Start button
2. Type `powershell`
3. Right-click on "Windows PowerShell" 
4. Click "Run as administrator"
5. Click "Yes" on the popup

**What you see:**
A blue PowerShell window with text like:
```
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

PS C:\Windows\system32>
```

**What to check:** The window title bar says "Administrator: Windows PowerShell"

---

## STEP 2: Install WSL2 and Ubuntu 24.04

**What you do:** Type this command in PowerShell and press Enter:

```powershell
wsl --install
```

**What happens:** Windows downloads WSL2 and Ubuntu 24.04. This takes 5-10 minutes.

**What you see:**
```
Installing: Windows Subsystem for Linux
Windows Subsystem for Linux is already installed.
Installing: Ubuntu
Ubuntu has been installed.
The operation completed successfully.
```

**What to check:** The command finishes without errors. If it says "already installed", that's fine.

---

## STEP 3: Restart Your Computer

**What you do:**
1. Click Start → Power → Restart
2. Wait for Windows to restart
3. Log in as usual

**What happens:** Windows finishes installing WSL2 components. The Ubuntu app will be in your Start menu.

**What to check:** You can log in and see your desktop.

---

## STEP 4: Open Ubuntu for the First Time

**What you do:**
1. Click the Start button
2. Type `ubuntu`
3. Click "Ubuntu 24.04 LTS" (NOT "Ubuntu" without a version)
4. Wait 2-3 minutes for the first-time setup

**What happens:** Ubuntu installs itself. It will ask you to create a username and password.

**What you see:**
```
Installing, this may take a few minutes...
Enter new UNIX username:
```

**What you do:** Type a username (lowercase, no spaces) and press Enter. Example: `john`

**What you see:**
```
Enter new UNIX username: john
New password:
```

**What you do:** Type a password and press Enter. **You will NOT see the password as you type.** This is normal.

**What you see:**
```
New password: 
Retype new password:
```

**What you do:** Type the same password again and press Enter.

**What you see:**
```
passwd: password updated successfully
Installation successful!
john@DESKTOP-XXXXXXX:~$
```

**What to check:** You see a prompt like `john@DESKTOP-XXXXXXX:~$`

---

## STEP 5: Update Ubuntu Packages

**What you do:** Type this command in the Ubuntu window and press Enter:

```bash
sudo apt-get update && sudo apt-get upgrade -y
```

**What happens:** Ubuntu downloads and installs the latest security updates. Takes 2-3 minutes.

**What you see:**
```
Hit:1 http://archive.ubuntu.com/ubuntu noble InRelease
Get:2 http://archive.ubuntu.com/ubuntu noble-updates InRelease
...
Reading package lists... Done
Building dependency tree... Done
...
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
```

**What to check:** The command finishes with "0 newly installed" or a list of packages that were updated. No red error text.

---

## STEP 6: Install the SHIELD-AI Project (ONE COMMAND)

**What you do:** Type this command in the Ubuntu window and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
```

**What happens:** This single command:
1. Installs Docker Engine
2. Installs OpenJDK 17 (for TLA+ model checker)
3. Installs kubectl (Kubernetes CLI)
4. Installs kind (local Kubernetes)
5. Installs Helm (Kubernetes package manager)
6. Clones the project repository
7. Pre-builds the Docker image (saves 5 minutes later)
8. Adds demo commands to your shell

**What you see (over 15-20 minutes):**
```
==> Pre-flight
    [ok] arch=x86_64, sudo ok, apt ok

==> [1/6] Docker Engine
    [skip] docker already installed  (or: [ok] docker installed: Docker version 24.0.7)

==> [2/6] OpenJDK 17 (for TLA+ TLC)
    [ok] openjdk-17 installed: openjdk version "17.0.12"

==> [3/6] kubectl 1.30
    [ok] kubectl installed: v1.30.0

==> [4/6] kind 0.23
    [ok] kind installed: kind v0.23.0

==> [5/6] Helm 3
    [ok] helm installed: v3.14.0

==> [6/6] Clone SHIELD-AI repo, pre-build image, add aliases
    [ok] cloned to /home/john/k8-auto-scaling-self-healing

==> Pre-building k8-ai-ops:dev (one-time, ~5 min)
    [ok] k8-ai-ops:dev image built

==> Bootstrap complete!
```

**What to check:** The last line says "Bootstrap complete!" with no red error text.

---

## STEP 7: Activate the New Settings

**What you do:** 
1. **Close the Ubuntu window completely**
2. Open the Start menu
3. Type `ubuntu`
4. Click "Ubuntu 24.04 LTS" again
5. Wait for it to open

**What happens:** A new Ubuntu window opens with all the new tools available.

**What to check:** You see a prompt like `john@DESKTOP-XXXXXXX:~$`

---

## STEP 8: Run the 2-Minute Test

**What you do:** Type this command and press Enter:

```bash
demo-quick
```

**What happens:** The script displays 8 sections of evidence:
1. TLA+ safety shield (273,702 states)
2. Composition theorem (53 states)
3. ML-only counterexample (93 states)
4. Live audit log
5. Shield stress audit
6. N=10 statistics report
7. **The strongest claim: every paper number traces to evidence**
8. IEEE paper PDF

**What you see (at the end):**
```
============================================================
  [7/8] STRONGEST CLAIM: every paper number traces to evidence-freeze.md
============================================================
------------------------------------------------------------
Running python3 scripts/_phase5_audit.py ...
------------------------------------------------------------
SOURCED (in both main + EF): 56
UNSOURCED (in main, NOT in EF): 0
============================================================
  DONE
============================================================
```

**What to check:** You see **"SOURCED (in both main + EF): 56"** and **"UNSOURCED (in main, NOT in EF): 0"**

**If you see this, the project is working correctly.** ✓

---

## STEP 9: Run the Full 15-Minute Demo (Optional)

**What you do:** Type this command and press Enter:

```bash
demo
```

**What happens:** The script runs 12 steps:
1. Creates a local Kubernetes cluster
2. Builds and loads the Docker image
3. Deploys Kafka, Prometheus, and the workload
4. Starts the 4-service AI pipeline
5. Sends baseline traffic (5 min)
6. Sends burst traffic (5 min)
7. Sends rampdown traffic (3 min)
8. Injects a fault and watches the system heal
9. Runs the TLA+ model checker
10. Exports graphs and statistics

**What you see (at the end):**
```
================================================
   SHIELD-AI golden run completed successfully
================================================
```

**What to check:** The command finishes with "SHIELD-AI golden run completed successfully"

---

## DAILY COMMANDS (After Setup)

| Command | What it does | Time |
|---------|--------------|------|
| `demo-help` | Print the cheat-sheet | instant |
| `demo-quick` | 2-min evidence display | 2 min |
| `demo` | Full 15-min live demo | 15 min |
| `demo-reset` | Wipe cluster and start fresh | 5 min |
| `tlac` | Run TLA+ model checker only | 4 min |
| `paper` | Open the IEEE paper PDF | instant |

---

## TROUBLESHOOTING

### Problem: "wsl --install" does nothing

**Fix:** Open PowerShell as Administrator (not just regular PowerShell).

---

### Problem: Ubuntu asks for password but you never set one

**Fix:** Windows requires your user account to have a password. Go to Settings → Accounts → Sign-in options → Password → Add. Then uninstall Ubuntu and reinstall:
```powershell
wsl --unregister Ubuntu
wsl --install
```

---

### Problem: "docker: command not found" after bootstrap

**Fix:** You need to open a NEW terminal window. The docker group membership only applies to new sessions.

---

### Problem: "permission denied" when running docker commands

**Fix:** Type this command once:
```bash
newgrp docker
```

---

### Problem: "kubectl: command not found"

**Fix:** Type this command:
```bash
source ~/.bashrc
```

---

### Problem: bootstrap script fails partway through

**Fix:** Just run it again. The script is idempotent (safe to re-run):
```bash
curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash
```

---

### Problem: demo-quick shows "SOURCED=55" instead of 56

**Fix:** This is a known issue. The project is still working. Check that the last line says "UNSOURCED (in main, NOT in EF): 0". If it does, the project is fine.

---

### Problem: Everything is broken

**Fix:** Nuclear option. Wipe everything and start fresh:
```bash
cd ~/k8-auto-scaling-self-healing
docker stop $(docker ps -aq) 2>/dev/null
docker system prune -af
git fetch --tags
git checkout v1.0-handover
bash bootstrap.sh
demo-quick
```

---

## WHAT TO DO NEXT

After `demo-quick` works:

1. **Read HANDOVER.md** for the full project guide:
   ```bash
   cat ~/k8-auto-scaling-self-healing/HANDOVER.md
   ```

2. **Read the paper:**
   ```bash
   xdg-open ~/k8-auto-scaling-self-healing/docs/paper/main.pdf
   ```

3. **Explore the code:**
   ```bash
   cd ~/k8-auto-scaling-self-healing
   ls
   ```

4. **Run the full demo when ready:**
   ```bash
   demo
   ```

---

## CONTACT

If you're stuck and the troubleshooting section doesn't help, contact the person who sent you this guide. They will need:
- The exact error message (copy-paste from the terminal)
- Which step you were on
- What you see when you type: `uname -a`
