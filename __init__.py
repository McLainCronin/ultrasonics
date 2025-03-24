"""
ultrasonics package
"""

# Levenshtein compatibility layer
try:
    from .tools import levenshtein_compat
except ImportError:
    pass