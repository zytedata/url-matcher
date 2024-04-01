import pytest

from url_matcher.patterns import PatternMatcher

from .util import load_json_fixture

PATTERNS_FIXTURE = load_json_fixture("single_patterns")
CORNER_CASES_FIXTURE = load_json_fixture("single_patterns_corner_cases")


@pytest.mark.parametrize(
    "pattern,match,no_match",
    [(row["pattern"], row["match"], row["no_match"]) for row in PATTERNS_FIXTURE],
    ids=[row["description"] for row in PATTERNS_FIXTURE],
)
def test_single_patterns(pattern, match, no_match):
    matcher = PatternMatcher(pattern)
    for url in match:
        assert matcher.match(url)
    for url in no_match:
        assert not matcher.match(url)


@pytest.mark.parametrize(
    "pattern,match,no_match",
    [(row["pattern"], row["match"], row["no_match"]) for row in CORNER_CASES_FIXTURE],
    ids=[row["description"] for row in CORNER_CASES_FIXTURE],
)
def test_single_patterns_corner_cases(pattern, match, no_match):
    matcher = PatternMatcher(pattern)
    for url in match:
        assert matcher.match(url)
    for url in no_match:
        assert not matcher.match(url)


def test_pattern_matcher_warning():
    with pytest.warns(SyntaxWarning):
        matcher = PatternMatcher("example.com/path?*_id=34")
        assert matcher.match("http://example.com/path?_id=34")
        assert not matcher.match("http://example.com/path?a_id=34")
