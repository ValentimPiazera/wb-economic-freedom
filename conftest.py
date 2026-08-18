"""Puts the repository root on `sys.path` so tests can `from src import ...`.

Mirrors how the notebooks run: with the repository root as the working
directory, no packaging step and no path manipulation in the test files.
"""
