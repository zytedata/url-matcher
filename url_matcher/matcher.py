"""
The matcher module contains the UrlMatcher class.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from itertools import chain
from typing import Any

from url_matcher.patterns import PatternMatcher, get_pattern_domain, hierarchical_str
from url_matcher.util import get_domain


@dataclass(init=False, frozen=True)
class Patterns:
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    priority: int

    def __init__(self, include: list[str], exclude: list[str] | None = None, priority: int = 500):
        # The initialization is manually set so that we can support an API of
        # accepting and returning lists. However, tuples are being used underneath
        # that class so that the attributes are truly immutable, in addition to
        # being frozen=True.
        # Using lists are far less likely to have human typing mistakes compared to
        # tuples since the trailing `,` char can easily be missed out. For
        # example:
        #     *  ("element") is not the same as ("element",) which is a tuple.
        # Lastly, the manner of how we set the attribute values below is in line
        # with how Python's own `dataclasses` library assign attributes to frozen
        # classes. Here's a reference:
        #     * https://github.com/python/cpython/blob/v3.10.2/Lib/dataclasses.py#L1117-L1120
        object.__setattr__(self, "include", tuple(include))
        object.__setattr__(self, "exclude", tuple(exclude or []))
        object.__setattr__(self, "priority", priority)

    def get_domains(self) -> list[str]:
        domains = [get_pattern_domain(pattern) for pattern in self.include]
        # remove duplicate domains preserving the order
        return list(dict.fromkeys(domain for domain in domains if domain))

    def get_includes_without_domain(self) -> list[str]:
        return [pattern for pattern in self.include if get_pattern_domain(pattern) is None]

    def all_includes_have_domain(self) -> bool:
        """Return true if all the include patterns have a domain"""
        return not self.get_includes_without_domain()

    def is_universal_pattern(self) -> bool:
        """Return true if there are no include patterns or they are empty. A universal pattern matches any domain"""
        for pattern in self.include:
            if pattern:
                return False
        return True

    def get_includes_for(self, domain: str) -> list[str]:
        return [pattern for pattern in self.include if get_pattern_domain(pattern) == domain]


@dataclass
class PatternsMatcher:
    identifier: Any
    patterns: Patterns
    include_matchers: list[PatternMatcher] = field(init=False)
    exclude_matchers: list[PatternMatcher] = field(init=False)

    def __post_init__(self):
        self.include_matchers = [PatternMatcher(pattern) for pattern in self.patterns.include]
        self.exclude_matchers = [PatternMatcher(pattern) for pattern in self.patterns.exclude]

    def match(self, url: str) -> bool:
        if self.include_matchers:
            for include in self.include_matchers:
                if include.match(url):
                    break
            else:
                return False
        for exclude in self.exclude_matchers:
            if exclude.match(url):
                return False
        return True


class IncludePatternsWithoutDomainError(ValueError):
    def __init__(self, *args, identifier: Any, patterns: Patterns, wrong_patterns: list[str]):
        super().__init__(*args)
        self.id = identifier
        self.patterns = patterns
        self.wrong_patterns = wrong_patterns


class URLMatcher:
    def __init__(self, data: Mapping[Any, Patterns] | Iterable[tuple[Any, Patterns]] | None = None):
        """
        A class that matches URLs against a list of patterns, returning
        the identifier of the rule that matched the URL.

        Example usage::

            matcher = URLMatcher()
            matcher.add_or_update(1, Patterns(include=["example.com/product"]))
            matcher.add_or_update(2, Patterns(include=["other.com"]))

            assert matcher.match("http://example.com/product/a_product.html") == 1
            assert matcher.match("http://other.com/a_different_page") == 2

        :param data: A map or a list of tuples with identifier, patterns pairs to
                     initialize the object from
        """
        self.matchers_by_domain: dict[str, list[PatternsMatcher]] = {}
        self.matchers_universal: list[PatternsMatcher] = []
        self.patterns: dict[Any, Patterns] = {}

        if data:
            items = data.items() if isinstance(data, Mapping) else data
            for identifier, patterns in items:
                self.add_or_update(identifier, patterns)

    def add_or_update(self, identifier: Any, patterns: Patterns):
        if not patterns.all_includes_have_domain() and not patterns.is_universal_pattern():
            wrong_patterns = [p for p in patterns.get_includes_without_domain() if p]
            raise IncludePatternsWithoutDomainError(
                f"All include patterns must belong to a domain "
                f"but the patterns {wrong_patterns} doesn't. "
                f"For example, the include pattern '/product/* "
                f"is invalid whereas the pattern 'example.com/product/*' isn't. "
                f"The only exception is the empty pattern which matches everything "
                f"and it is allowed. "
                f"identifier: {identifier}.",
                identifier=identifier,
                patterns=patterns,
                wrong_patterns=wrong_patterns,
            )
        if identifier in self.patterns:
            self.remove(identifier)
        self.patterns[identifier] = patterns
        matcher = PatternsMatcher(identifier, patterns)
        for domain in patterns.get_domains():
            self._add_matcher(domain, matcher)
        if patterns.is_universal_pattern():
            self._add_matcher("", matcher)

    def remove(self, identifier: Any):
        patterns = self.patterns.get(identifier)
        if not patterns:
            return
        del self.patterns[identifier]
        for domain in patterns.get_domains():
            self._del_matcher(domain, identifier)
        if patterns.is_universal_pattern():
            self._del_matcher("", identifier)

    def get(self, identifier: Any) -> Patterns | None:
        return self.patterns.get(identifier)

    def match(self, url: str, *, include_universal=True) -> Any | None:
        return next(self.match_all(url, include_universal=include_universal), None)

    def match_all(self, url: str, *, include_universal=True) -> Iterator[Any]:
        domain = get_domain(url)
        matchers: Iterable[PatternsMatcher] = self.matchers_by_domain.get(domain) or []
        if include_universal:
            matchers = chain(matchers, self.matchers_universal)
        for matcher in matchers:
            if matcher.match(url):
                yield matcher.identifier

    def match_universal(self) -> Iterator[Any]:
        return (m.identifier for m in self.matchers_universal)

    def _sort_domain(self, domain: str):
        """
        Sort all the rules within a domain so that the matching can be done in sequence:
        the first rule matching wins.

        A total ordering is defined. This is ensured by using including
        the identifier in the sorting criteria

        Sorting criteria:
          * Priority (descending)
          * Sorted list of includes for this domain (descending)
          * Rule identifier (descending)
        """

        def sort_key(matcher: PatternsMatcher) -> tuple:
            sorted_includes = sorted(map(hierarchical_str, matcher.patterns.get_includes_for(domain)))
            return (matcher.patterns.priority, sorted_includes, matcher.identifier)

        self.matchers_by_domain[domain].sort(key=sort_key, reverse=True)
        self.matchers_universal.sort(key=sort_key, reverse=True)

    def _del_matcher(self, domain: str, identifier: Any):
        matchers = self.matchers_by_domain[domain]
        for idx in range(len(matchers)):
            if matchers[idx].identifier == identifier:
                del matchers[idx]
                break
        if not matchers:
            del self.matchers_by_domain[domain]
        for idx in range(len(self.matchers_universal)):
            if self.matchers_universal[idx].identifier == identifier:
                del self.matchers_universal[idx]
                break

    def _add_matcher(self, domain: str, matcher: PatternsMatcher):
        # FIXME: This can be made much more efficient if we insert the data directly in order instead of resorting.
        # The bisect module could be used for this purpose.
        # I'm leaving it for the future as insertion time is not critical.
        self.matchers_by_domain.setdefault(domain, []).append(matcher)
        if domain == "":
            self.matchers_universal.append(matcher)
        self._sort_domain(domain)
