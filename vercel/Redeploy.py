#!/usr/bin/env python3
"""
Deployment script for TradingView MCP to Vercel.
Checks for required environment variables and Vercel CLI, then deploys.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required environment variables
REQUIRED_ENV_VARS = [
    "TRADINGVIEW_COOKIE",
    "VERCEL_URL",
    "TRADINGVIEW_URL",
]

def check_env_vars():
    """Check if all required environment variables are set."""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please set them in your .env file.")
        return False
    print("✅ All required environment variables are set.")
    return True

def check_vercel_cli():
    """Check if Vercel CLI is installed."""
    try:
        result = subprocess.run("vercel --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Vercel CLI is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Vercel CLI is not working properly.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        print("❌ Vercel CLI is not installed. Please install it with: npm install -g vercel")
        return False

def deploy():
    """Deploy to Vercel."""
    print("🚀 Deploying to Vercel...")
    try:
        result = subprocess.run("vercel --prod", shell=True, cwd=os.getcwd())
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
    
    deploy()

if __name__ == "__main__":
    main()