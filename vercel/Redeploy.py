"""
Deployment script for TradingView MCP to Vercel.
Syncs local .env variables to Vercel Project Settings and then deploys.
"""

import os
import sys
import subprocess
from dotenv import dotenv_values

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

def push_env_vars():
    """
    Reads .env and pushes variables to Vercel Production environment.
    Uses 'vercel env add' command.
    """
    print("🔄 Syncing environment variables to Vercel...")
    
    # Load variables specifically from the .env file
    env_vars = dotenv_values(".env")
    
    for key, value in env_vars.items():
        # Skip empty lines or comments if any slipped through
        if not key or not value:
            continue
            
        print(f"   - Updating {key}...", end=" ", flush=True)
        
        # 1. Remove existing variable to avoid "already exists" errors
        # We suppress output because it errors if the var doesn't exist, which is fine
        subprocess.run(
            f'vercel env rm {key} production -y', 
            shell=True, 
            capture_output=True
        )
        
        # 2. Add the new variable
        # passing input=value allows us to pipe the value into the command prompt
        try:
            cmd = f'vercel env add {key} production'
            # The 'vercel env add' command expects the value via stdin usually
            process = subprocess.run(
                cmd,
                input=str(value), # Pass the value into the prompt
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

    print("✨ Environment variables synced successfully.")

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
        
    # NEW STEP: Sync Env Vars
    push_env_vars()
    
    deploy()

if __name__ == "__main__":
    main()