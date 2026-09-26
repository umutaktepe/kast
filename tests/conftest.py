"""Global pytest configuration and fixtures for Kast test suite."""

import os

# Ensure Qt tests always run offscreen in CI and headless environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
