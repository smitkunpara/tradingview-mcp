import pytest
import sys
import os
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path so we can import vercel.index and src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from vercel.index import app
from src.tradingview_mcp.config import settings

@pytest.fixture
def client():
    """Create a TestClient instance"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Get valid client authentication headers"""
    return {"X-Client-Key": settings.CLIENT_API_KEY}

@pytest.fixture
def admin_headers():
    """Get valid admin authentication headers"""
    return {"X-Admin-Key": settings.ADMIN_API_KEY}
