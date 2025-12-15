"""
Deployment script for TradingView MCP to Vercel.
Generates requirements.txt from pyproject.toml, syncs local .env variables to Vercel Project Settings, and then deploys.
"""

import os
import sys
import subprocess
from dotenv import dotenv_values
from pathlib import Path

# Required environment variables to check
REQUIRED_ENV_VARS = [
    "TRADINGVIEW_COOKIE",
    "VERCEL_URL",
    "TRADINGVIEW_URL",
    "TV_ADMIN_KEY",
    "TV_CLIENT_KEY"
]

def check_env_vars():
    """Check if all required environment variables are set locally."""
    # dotenv_values loads vars from .env file directly (not os.environ)
    config = dotenv_values(".env")
    missing = []
    
    for var in REQUIRED_ENV_VARS:
        if var not in config or not config[var]:
            missing.append(var)
            
    if missing:
        print(f"❌ Missing required environment variables in .env: {', '.join(missing)}")
        return False
    print("✅ All required environment variables are present locally.")
    return True

def check_vercel_cli():
    """Check if Vercel CLI is installed."""
    try:
        result = subprocess.run("vercel --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Vercel CLI detected: {result.stdout.strip()}")
            return True
        else:
            print("❌ Vercel CLI is not working properly.")
            return False
    except Exception:
        print("❌ Vercel CLI is not installed. Install via: npm install -g vercel")
        return False


def ensure_uv_lock(project_root: Path, lock_path: Path):
    """Ensure `uv.lock` exists. Try to generate it using the `uv` CLI if missing.

    This is best-effort: we try a few common `uv` commands to create/update
    the lockfile. If the `uv` CLI is not installed or all attempts fail,
    the function will return False and print instructions for manual steps.
    """
    if lock_path.exists():
        print(f"🔒 Found existing uv.lock at {lock_path} — will use existing lockfile.")
        return True

    print("🔧 No uv.lock found — attempting to generate one locally using `uv`...")

    # Check if `uv` CLI is available
    try:
        uv_check = subprocess.run("uv --version", shell=True, capture_output=True, text=True)
        if uv_check.returncode != 0:
            print("⚠️  `uv` CLI not found locally. Install it to auto-generate uv.lock or create uv.lock manually.")
            print("   Install: pip install uv")
            return False
    except Exception:
        print("⚠️  Could not run `uv --version`. Is `uv` installed and on PATH?")
        return False

    # Try a sequence of commands that may create a lockfile. These are best-effort;
    # different versions of `uv` expose slightly different flags.
    candidates = [
        "uv lock",
        "uv lock --output uv.lock",
        "uv lock -o uv.lock",
        "uv add --lock",
        "uv add --lock-file uv.lock",
    ]

    for cmd in candidates:
        print(f"   -> Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, cwd=str(project_root), capture_output=True, text=True)
            if result.returncode == 0:
                if lock_path.exists():
                    print("✅ uv.lock generated successfully.")
                    return True
                # sometimes uv writes to stdout or another path; check for typical output
                if "lock" in (result.stdout or "").lower():
                    print("✅ uv command completed; check uv.lock in repo root.")
                    if lock_path.exists():
                        return True
            else:
                print(f"   (failed) {result.stderr.splitlines()[-1] if result.stderr else result.stdout}")
        except Exception as e:
            print(f"   Exception running {cmd}: {e}")

    print("❌ Failed to auto-generate uv.lock. Options:")
    print("   1) Install `uv` locally and run `uv lock` in the repo root to produce uv.lock.")
    print("   2) Commit an existing uv.lock from a reproducible environment and push before deploying.")
    print("   3) Change `vercel.json` to use `pip` installer instead of `uv` if you prefer pip-based builds.")
    return False

def push_env_vars(force: bool = False):
    """
    Reads .env and pushes variables to Vercel Production environment.
    Uses 'vercel env add' command.
    """
    print("🔄 Syncing environment variables to Vercel...")

    # Load variables specifically from the .env file
    env_vars = dotenv_values(".env")

    # Query existing environment variable names in Vercel (production) once
    try:
        ls = subprocess.run(
            "vercel env ls production",
            shell=True,
            capture_output=True,
            text=True
        )
        vercel_envs_out = ls.stdout or ""
    except Exception:
        vercel_envs_out = ""

    def exists_on_vercel(varname: str) -> bool:
        # crude but effective: check if the var name appears at the start of any line
        for line in vercel_envs_out.splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == varname:
                return True
        return False

    for key, value in env_vars.items():
        # Skip empty lines or comments if any slipped through
        if not key or not value:
            continue

        # If not forcing, skip variables that already exist to preserve previous values
        if not force and exists_on_vercel(key):
            print(f"   - Skipping {key} (already set on Vercel)")
            continue

        print(f"   - Setting {key}...", end=" ", flush=True)

        try:
            if force:
                # Remove existing variable first (ignore errors)
                subprocess.run(f'vercel env rm {key} production -y', shell=True, capture_output=True)

            cmd = f'vercel env add {key} production'
            process = subprocess.run(
                cmd,
                input=str(value),
                shell=True,
                capture_output=True,
                text=True
            )

            if process.returncode == 0:
                print("✅")
            else:
                print(f"❌ Error: {process.stderr.strip()}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print("✨ Environment variables processed.")

def deploy():
    """Deploy to Vercel."""
    print("🚀 Deploying to Vercel...")
    try:
        # --prod triggers a production deployment
        result = subprocess.run("vercel --prod", shell=True)
        if result.returncode == 0:
            print("✅ Deployment successful!")
        else:
            print("❌ Deployment failed.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error during deployment: {e}")
        sys.exit(1)

def main():
    print("🔍 Checking deployment prerequisites...")
    
    if not check_env_vars():
        sys.exit(1)
    
    if not check_vercel_cli():
        sys.exit(1)
    
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    lock_path = project_root / "uv.lock"

    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found at {pyproject_path}. Aborting — uv requires a pyproject.toml.")
        sys.exit(1)

    # Ensure lockfile if using uv installer flow
    if lock_path.exists():
        print(f"🔒 Found existing uv.lock at {lock_path} — proceeding with uv-only deployment flow.")
    else:
        # Try to generate uv.lock automatically (best-effort)
        if not ensure_uv_lock(project_root, lock_path):
            print("❌ No uv.lock found at repo root; uv-only deploys require a lockfile. Aborting.")
            sys.exit(1)
        
    # STEP 2: Sync Env Vars
    # Ask user whether to keep previous Vercel envs or upload new ones.
    try:
        answer = input("Use previous Vercel env values? (Y/n): ").strip().lower()
    except Exception:
        # Non-interactive environment: default to keep previous values
        answer = "y"

    # Interpret empty or 'y' as yes (use previous). 'n' means upload/replace new envs.
    force_upload = True if answer == "n" else False
    if force_upload:
        print("ℹ️  Will upload and replace environment variables on Vercel.")
    else:
        print("ℹ️  Keeping existing Vercel environment variables (skipping upload).")

    push_env_vars(force=force_upload)
    
    # STEP 3: Deploy
    deploy()

if __name__ == "__main__":
    main()