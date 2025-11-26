"""Pytest configuration and fixtures"""

import pytest
from hypothesis import settings

# Configure Hypothesis to run at least 100 iterations for property tests
settings.register_profile("default", max_examples=100)
settings.load_profile("default")
