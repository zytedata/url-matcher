import pytest

from url_matcher import Patterns, URLMatcher
from url_matcher.matcher import IncludePatternsWithoutDomainError

from .util import load_json_fixture

PATTERNS_FIXTURE = load_json_fixture("patterns")
CORNER_CASES_FIXTURE = load_json_fixture("patterns_corner_cases")
RULES_FIXTURE = load_json_fixture("rules")


@pytest.mark.parametrize(
    ("patterns", "match", "no_match"),
    [(row["patterns"], row["match"], row["no_match"]) for row in PATTERNS_FIXTURE],
    ids=[row["description"] for row in PATTERNS_FIXTURE],
)
def test_matcher_single_rule(patterns, match, no_match):
    matcher = URLMatcher()
    matcher.add_or_update(23, Patterns(**patterns))
    for url in match:
        assert matcher.match(url) == 23
        assert list(matcher.match_all(url)) == [23]
    for url in no_match:
        assert not matcher.match(url)
        assert list(matcher.match_all(url)) == []


@pytest.mark.parametrize(
    ("patterns", "match", "no_match"),
    [(row["patterns"], row["match"], row["no_match"]) for row in CORNER_CASES_FIXTURE],
    ids=[row["description"] for row in CORNER_CASES_FIXTURE],
)
def test_matcher_single_rule_corner_cases(patterns, match, no_match):
    matcher = URLMatcher()
    matcher.add_or_update(23, Patterns(**patterns))
    for url in match:
        assert matcher.match(url) == 23
        assert list(matcher.match_all(url)) == [23]
    for url in no_match:
        assert not matcher.match(url)
        assert list(matcher.match_all(url)) == []


@pytest.mark.parametrize(
    ("rules", "cases"),
    [(row["rules"], row["cases"]) for row in RULES_FIXTURE],
    ids=[row["description"] for row in RULES_FIXTURE],
)
def test_matcher_rules(rules, cases):
    matcher = URLMatcher()
    for id, patterns in rules:
        matcher.add_or_update(id, Patterns(**patterns))
    for url, id in cases:
        assert matcher.match(url) == id


def test_matcher_init():
    rules = {
        1: Patterns(["example.com"]),
        2: Patterns(["other.com"]),
    }
    matcher1 = URLMatcher(rules)
    matcher2 = URLMatcher(rules.items())
    for matcher in [matcher1, matcher2]:
        assert matcher.match("http://example.com") == 1
        assert matcher.match("http://other.com") == 2
        assert matcher.match("http://non-match") is None


def test_matcher_add_remove_get():
    matcher = URLMatcher()
    patterns = Patterns(["example.com"])
    matcher.add_or_update(1, patterns)
    assert matcher.match("http://example.com") == 1
    assert matcher.get(1) is patterns
    assert list(matcher.match_universal()) == []

    patterns_3 = Patterns(["example.com/articles"])
    matcher.add_or_update(3, patterns_3)
    assert matcher.match("http://example.com/articles") == 3
    assert matcher.get(3) is patterns_3

    # Testing update
    patterns = Patterns(["example.com/products"])
    matcher.add_or_update(1, patterns)
    assert matcher.match("http://example.com") is None
    assert matcher.match("http://example.com/products") == 1
    assert matcher.get(1) is patterns

    # Testing universal patterns
    univ_patterns = Patterns([""])
    matcher.add_or_update(2, univ_patterns)
    assert matcher.match("http://example.com") == 2
    assert matcher.match("http://example.com/products") == 1
    assert matcher.get(2) is univ_patterns
    assert list(matcher.match_universal()) == [2]

    # Removing a universal pattern
    matcher.remove(2)
    assert matcher.match("http://example.com") is None
    assert matcher.match("http://example.com/products") == 1
    assert matcher.get(2) is None
    assert list(matcher.match_universal()) == []

    # Removing regular patterns
    matcher.remove(3)
    assert matcher.match("http://example.com/products") == 1
    assert matcher.match("http://example.com/articles") is None
    assert matcher.get(3) is None

    matcher.remove(1)
    assert matcher.match("http://example.com/products") is None
    assert matcher.get(1) is None
    assert len(matcher.matchers_by_domain) == 0
    assert len(matcher.patterns) == 0

    # Wrong patterns
    with pytest.raises(IncludePatternsWithoutDomainError):
        matcher.add_or_update(1, Patterns(["/no_domain_pattern"]))

    # Patterns with the same domain shouldn't produce multiple matchers
    patterns = Patterns(["example.com/products", "example.com/brands"])
    matcher.add_or_update(1, patterns)
    assert len(matcher.matchers_by_domain) == 1
    assert len(matcher.matchers_by_domain["example.com"]) == 1
    assert len(matcher.patterns) == 1
    assert matcher.match("http://example.com") is None
    assert matcher.match("http://example.com/products") == 1
    assert matcher.match("http://example.com/brands") == 1
    assert len(list(matcher.match_all("http://example.com/products"))) == 1


def test_dedupe_unique_patterns():
    p = [
        Patterns(["example.com"]),
        Patterns(include=["example.com"], exclude=None, priority=500),
    ]
    assert len(set(p)) == 1

    p.append(Patterns(["example.com"], priority=1))
    assert len(set(p)) == 2


def test_patterns_immutability():
    p = Patterns(["example.com"])

    with pytest.raises(AttributeError):
        p.priority = 1  # type: ignore[misc]


def test_match_all():
    matcher = URLMatcher()
    matcher.add_or_update(1, Patterns(include=["example.com"]))
    matcher.add_or_update(2, Patterns(include=["foo.example.com"]))
    matcher.add_or_update(3, Patterns(include=["bar.example.com/products"]))
    matcher.add_or_update(4, Patterns(include=["bar.example.com"]))

    assert list(matcher.match_all("http://example.com")) == [1]
    assert list(matcher.match_all("http://foo.example.com")) == [2, 1]
    assert list(matcher.match_all("http://bar.example.com")) == [4, 1]
    assert list(matcher.match_all("http://example.com/products")) == [1]
    assert list(matcher.match_all("http://foo.example.com/products")) == [2, 1]
    assert list(matcher.match_all("http://bar.example.com/products")) == [3, 4, 1]


def test_match_all_include_universal():
    matcher = URLMatcher()
    matcher.add_or_update(1, Patterns(include=["example.com"]))
    matcher.add_or_update(2, Patterns(include=[]))
    matcher.add_or_update(3, Patterns(include=["foo.example.com"]))
    matcher.add_or_update(4, Patterns(include=[""]))
    assert list(matcher.match_all("http://example.com")) == [1, 4, 2]
    assert list(matcher.match_all("http://example.com", include_universal=False)) == [1]
    assert list(matcher.match_all("http://foo.example.com")) == [3, 1, 4, 2]
    assert list(matcher.match_all("http://foo.example.com", include_universal=False)) == [3, 1]
    assert list(matcher.match_all("http://example.net")) == [4, 2]
    assert list(matcher.match_all("http://example.net", include_universal=False)) == []


def test_match_universal():
    matcher = URLMatcher()
    matcher.add_or_update(1, Patterns(include=["example.com"]))
    matcher.add_or_update(2, Patterns(include=[]))
    matcher.add_or_update(3, Patterns(include=["foo.example.com"]))
    matcher.add_or_update(4, Patterns(include=[""]))
    assert list(matcher.match_universal()) == [4, 2]
