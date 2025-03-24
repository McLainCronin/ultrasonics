from rapidfuzz import fuzz, process

def fuzzy_match(query, choices, limit=1):
    """Find the best match for a query string in a list of choices."""
    return process.extract(query, choices, limit=limit)

def fuzzy_ratio(s1, s2):
    """Calculate the fuzzy ratio between two strings."""
    return fuzz.ratio(s1, s2)

def fuzzy_partial_ratio(s1, s2):
    """Calculate the partial fuzzy ratio between two strings."""
    return fuzz.partial_ratio(s1, s2)

def fuzzy_token_sort_ratio(s1, s2):
    """Calculate the token sort ratio between two strings."""
    return fuzz.token_sort_ratio(s1, s2) 