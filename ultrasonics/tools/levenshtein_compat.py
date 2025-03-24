"""
Levenshtein compatibility layer for ultrasonics.
This provides a bridge between fuzzywuzzy and rapidfuzz.
"""

try:
    # Try original Levenshtein first
    import Levenshtein
except ImportError:
    # Fall back to rapidfuzz
    from rapidfuzz import distance, fuzz
    
    class LevenshteinCompat:
        def ratio(s1, s2):
            return fuzz.ratio(s1, s2)
        
        def distance(s1, s2):
            return distance.Levenshtein.distance(s1, s2)
    
    Levenshtein = LevenshteinCompat