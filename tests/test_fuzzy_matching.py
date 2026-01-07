"""
Tests for fuzzy matching normalization and confidence scoring.
"""

from spo.services.dedup import fuzzy_match_score


def test_exact_equivalence_variants():
    assert fuzzy_match_score("mediamarkt", "Media Markt") == 100.0
    assert fuzzy_match_score("MediaMarkt", "mediamarkt") == 100.0


def test_domain_normalization():
    # Domain should normalize to brand name
    assert fuzzy_match_score("mediamarkt", "mediamarkt.de") >= 98.0
    assert fuzzy_match_score("mediamarkt", "www.mediamarkt.com") >= 95.0


def test_generic_tokens_removed():
    # Generic suffixes like 'online shop' should not penalize heavily
    assert fuzzy_match_score("mediamarkt", "mediamarkt online shop") >= 95.0
    assert fuzzy_match_score("mediamarkt", "mediamarkt club") >= 90.0


def test_noise_punctuation_whitespace():
    assert fuzzy_match_score("media-markt", "  media  markt  ") >= 98.0
