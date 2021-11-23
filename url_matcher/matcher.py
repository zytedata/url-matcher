"""
The matcher module contains the UrlMatcher class.
"""
from dataclasses import dataclass, field
from itertools import chain
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from url_matcher.patterns import PatternMatcher, get_pattern_domain, hierarchical_str
from url_matcher.util import get_domain


@dataclass
class Patterns:
    include: List[str]
    exclude: List[str] = field(default_factory=list)
    priority: int = 500

    def get_domains(self) -> List[str]:
        domains = [get_pattern_domain(pattern) for pattern in self.include]
        return [domain for domain in domains if domain]

    def get_includes_without_domain(self) -> List[str]:
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

    def get_includes_for(self, domain):
        return [pattern for pattern in self.include if get_pattern_domain(pattern) == domain]


@dataclass
class PatternsMatcher:
    id: Any
    patterns: Patterns
    include_matchers: List[PatternMatcher] = field(init=False)
    exclude_matchers: List[PatternMatcher] = field(init=False)

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
    def __init__(self, *args, id: Any, patterns: Patterns, wrong_patterns: List[str]):
        super().__init__(*args)
        self.id = id
        self.patterns = patterns
        self.wrong_patterns = wrong_patterns


class URLMatcher:
    def __init__(self, data: Union[Mapping[Any, Patterns], Iterable[Tuple[Any, Patterns]], None] = None):
        """
        A class that matches URLs against a list of patterns, returning
        the identifier of the rule that matched the URL.

        Example usage::

            matcher = URLMatcher()
            matcher.add_or_update(1, Patterns(include=["example.com/product"]))
            matcher.add_or_update(2, Patterns(include=["other.com"]))

            assert matcher.match("http://example.com/product/a_product.html") == 1
            assert matcher.match("http://other.com/a_different_page") == 2

        :param data: A map or a list of tuples with id, patterns pairs to
                     initialize the object from
        """
        self.matchers_by_domain: Dict[str, List[PatternsMatcher]] = {}
        self.patterns: Dict[Any, Patterns] = {}

        if data:
            items = data.items() if isinstance(data, Mapping) else data
            for id, patterns in items:
                self.add_or_update(id, patterns)

    def add_or_update(self, id: Any, patterns: Patterns):
        if not patterns.all_includes_have_domain() and not patterns.is_universal_pattern():
            wrong_patterns = [p for p in patterns.get_includes_without_domain() if p]
            raise IncludePatternsWithoutDomainError(
                f"All include patterns must belong to a domain "
                f"but the patterns {wrong_patterns} doesn't. "
                f"For example, the include pattern '/product/* "
                f"is invalid whereas the pattern 'example.com/product/*' isn't. "
                f"The only exception is the empty pattern which matches everything "
                f"and it is allowed. "
                f"id: {id}.",
                id=id,
                patterns=patterns,
                wrong_patterns=wrong_patterns,
            )
        if id in self.patterns:
            self.remove(id)
        self.patterns[id] = patterns
        matcher = PatternsMatcher(id, patterns)
        for domain in patterns.get_domains():
            self._add_matcher(domain, matcher)
        if patterns.is_universal_pattern():
            self._add_matcher("", matcher)

    def remove(self, id: Any):
        patterns = self.patterns.get(id)
        if not patterns:
            return
        del self.patterns[id]
        for domain in patterns.get_domains():
            self._del_matcher(domain, id)
        if patterns.is_universal_pattern():
            self._del_matcher("", id)

    def get(self, id: Any) -> Optional[Patterns]:
        return self.patterns.get(id)

    def match(self, url: str) -> Optional[Any]:
        domain = get_domain(url)
        for matcher in chain(self.matchers_by_domain.get(domain) or [], self.matchers_by_domain.get("") or []):
            if matcher.match(url):
                return matcher.id
        return None

    def _sort_domain(self, domain: str):
        """
        Sort all the rules within a domain so that the matching can be done in sequence:
        the first rule matching wins.

        A total ordering is defined. This is ensured by using including
        the id in the sorting criteria

        Sorting criteria:
          * Priority (descending)
          * Sorted list of includes for this domain (descending)
          * Rule id (descending)
        """

        def sort_key(matcher: PatternsMatcher):
            sorted_includes = sorted(map(hierarchical_str, matcher.patterns.get_includes_for(domain)))
            return (matcher.patterns.priority, sorted_includes, matcher.id)

        self.matchers_by_domain[domain].sort(key=sort_key, reverse=True)

    def _del_matcher(self, domain: str, id: Any):
        matchers = self.matchers_by_domain[domain]
        for idx in range(len(matchers)):
            if matchers[idx].id == id:
                del matchers[idx]
                break
        if not matchers:
            del self.matchers_by_domain[domain]

    def _add_matcher(self, domain: str, matcher: PatternsMatcher):
        # FIXME: This can be made much more efficient if we insert the data directly in order instead of resorting.
        # The bisect module could be used for this purpose.
        # I'm leaving it for the future as insertion time is not critical.
        self.matchers_by_domain.setdefault(domain, []).append(matcher)
        self._sort_domain(domain)
