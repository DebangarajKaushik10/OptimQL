"""Pytest configuration - ensures the project root is on sys.path."""
import sys
from pathlib import Path

# Add the project root to sys.path so 'backend' package is importable
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
