#!/usr/bin/env python3
"""pytest configuration for Video Pipeline tests."""

import sys
from pathlib import Path

# Add execution directory to path for imports
execution_dir = Path(__file__).parent.parent / "execution"
sys.path.insert(0, str(execution_dir))
