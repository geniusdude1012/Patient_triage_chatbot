"""
conftest.py
────────────
pytest configuration file.
Adds project root to sys.path so all Backend imports
work correctly when pytest runs from any directory.
"""
 
import sys
import os
 
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


