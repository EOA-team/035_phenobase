"""
Docstring for test.test_ci
"""

from src.main import greet


def test_ci_works():
    """Test that the CI pipeline is working correctly."""
    assert True


def test_greet():
    """Test the greet function."""
    assert greet("World") == "Hello, World!"
