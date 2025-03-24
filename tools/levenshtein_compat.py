from rapidfuzz import Levenshtein

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings."""
    return Levenshtein.distance(s1, s2)

def levenshtein_ratio(s1, s2):
    """Calculate the Levenshtein ratio between two strings."""
    return Levenshtein.ratio(s1, s2) 