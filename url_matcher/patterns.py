"""
Utilities to parse patterns and match URLs using them.
"""

import ipaddress
import re
import warnings
from collections import namedtuple
from functools import lru_cache
from typing import Dict, Optional, Pattern, Tuple
from urllib.parse import parse_qs, urlparse

from url_matcher.util import get_domain


def get_pattern_domain(pattern: str) -> Optional[str]:
    """
    Returns the domain of the pattern if any.

    >>> get_pattern_domain("")

    >>> get_pattern_domain("/")

    >>> get_pattern_domain("dom")
    'dom'
    >>> get_pattern_domain("DOM")
    'dom'
    >>> get_pattern_domain("dom:80")
    'dom'
    >>> get_pattern_domain("http://dom:80")
    'dom'
    >>> get_pattern_domain("http://dom/a_path")
    'dom'
    """
    parsed = pattern_parse(pattern)
    if parsed.netloc:
        return get_domain(f"//{parsed.netloc}").lower()
    return None


def pattern_to_url(pattern: str) -> str:
    """
    Required for urlparse to recognize the domain in patterns
    like example.com/path

    >>> pattern_to_url("example.com/")
    '//example.com/'
    >>> pattern_to_url("example.com")
    '//example.com'
    >>> pattern_to_url("https://example.com")
    'https://example.com'
    >>> pattern_to_url("MySchema4+.-://example.com")
    'MySchema4+.-://example.com'
    >>> pattern_to_url("//example.com")
    '////example.com'
    """
    # As defined in https://datatracker.ietf.org/doc/html/rfc3986#section-3.1
    has_scheme = re.search(r"^([a-zA-Z][a-zA-Z0-9.+-]*:)?//", pattern)
    if not has_scheme:
        pattern = f"//{pattern}"
    elif pattern.startswith("//"):
        # This is required because urlparse("//example.com").netloc == "//example.com"
        # but instead we want it to be parsed into the the path. We achieve it by appending
        # two more slashes
        pattern = f"//{pattern}"
    return pattern


ParseTuple = namedtuple("ParseTuple", "scheme netloc path query fragment")


@lru_cache(30)
def pattern_parse(pattern: str) -> ParseTuple:
    """
    Parses the pattern to a named tuple (scheme, netloc, path, query, fragment)
    >>> pattern_parse("example.com")
    ParseTuple(scheme='', netloc='example.com', path='', query='', fragment='')
    >>> pattern_parse("//example.com/path;this_is_also_path")
    ParseTuple(scheme='', netloc='', path='//example.com/path;this_is_also_path', query='', fragment='')
    """
    pattern = pattern_to_url(pattern)
    return _urlparse(pattern)


def _urlparse(url: str) -> ParseTuple:
    """
    Returns a named tuple (scheme, netloc, path, query, fragment)
    where path and params are joined together into path and
    some other elements are normalized.

    >>> _urlparse("scheme://example.com/path;params?query=23#fragment")
    ParseTuple(scheme='scheme', netloc='example.com', path='/path;params', query='query=23', fragment='fragment')
    >>> _urlparse("http://example.com:80/path")
    ParseTuple(scheme='http', netloc='example.com', path='/path', query='', fragment='')
    """
    scheme, netloc, path, params, query, fragment = urlparse(url)
    path = _join_path_and_params(path, params)
    scheme, netloc = normalize_netloc_and_schema(scheme, netloc)
    return ParseTuple(scheme, netloc, path, query, fragment)


def _wildcard_re_escape(text: str):
    return re.escape(text).replace("\\*", ".*")


def _join_path_and_params(path, params):
    if params:
        return f"{path};{params}"
    else:
        return path


def normalize_netloc_and_schema(schema: str, netloc: str) -> Tuple[str, str]:
    """
    Removes 80 or 443 port when obvious. Deduces http or https when the port is provided

    >>> normalize_netloc_and_schema("http", "example.com:80")
    ('http', 'example.com')
    >>> normalize_netloc_and_schema("http", "example.com:80")
    ('http', 'example.com')
    >>> normalize_netloc_and_schema("http", "example.com:443")
    ('http', 'example.com:443')
    >>> normalize_netloc_and_schema("https", "example.com:443")
    ('https', 'example.com')
    >>> normalize_netloc_and_schema("", "example.com:80")
    ('http', 'example.com')
    >>> normalize_netloc_and_schema("", "example.com:443")
    ('https', 'example.com')
    """
    schema = schema.lower()
    domain, port = split_domain_port(netloc)
    if (port == "80" and schema in ("http", "")) or (port == "443" and schema in ("https", "")):
        return "http" if port == "80" else "https", domain
    else:
        return schema, netloc


def hierarchical_str(pattern: str):
    """
    Rewrites the given pattern in a string that is useful to sort patterns from more general to more concrete.
    For example, the pattern "example.com" is more general than "blog.example.com" which is more general than
    "blog.example.com/post/1"

    >>> hierarchical_str("http://blog.example.com/path?query=23#fragment")
    'com.example.blog/pathquery=23fragment'
    >>> hierarchical_str("http://blog.example.com:1234")
    'com.example.blog'
    >>> hierarchical_str("http://127.0.0.1:80/path")
    '127.0.0.1/path'
    """
    parsed = pattern_parse(pattern)
    netloc = parsed.netloc
    if ":" in parsed.netloc:
        netloc, _ = split_domain_port(parsed.netloc)
    try:
        ipaddress.ip_address(netloc)
        is_ip = True
    except ValueError:
        is_ip = False
    if not is_ip:
        # Reversing the domain so that higher levels are before
        # e.g. blog.example.com -> com.example.blog
        netloc = ".".join(reversed(netloc.split(".")))
    return "".join((netloc, *parsed[2:]))


def split_domain_port(netloc: str) -> Tuple[str, Optional[str]]:
    """
    Splits the netloc into domain and port.

    >>> split_domain_port("example.com")
    ('example.com', None)
    >>> split_domain_port("example.com:80")
    ('example.com', '80')
    """
    segments = netloc.split(":")
    if len(segments) > 1:
        return ":".join(segments[:-1]), segments[-1]
    return netloc, None


class PatternMatcher:
    def __init__(self, pattern: str):
        # Parsing and validation
        self.pattern = pattern
        self.parsed = pattern_parse(pattern)
        self.domain = get_pattern_domain(pattern)
        self.netloc_re: Optional[Pattern] = None
        self.path_re: Optional[Pattern] = None
        self.fragment_re: Optional[Pattern] = None
        self.query_re_dict: Optional[Dict[str, Pattern]] = None
        self._build_regexes()

    def _build_regexes(self):
        """
        Builds the compiled regexes that can be used to match the pattern.
        """
        pscheme, pnetloc, ppath, pquery, pfragment = self.parsed
        if pnetloc:
            netloc_re = re.escape(pnetloc)
            if not any((ppath, pquery, pfragment)):
                # Also match subdomains if there is no path, query or fragment in the pattern
                netloc_re = rf"(?:.*\.)?{netloc_re}"
            netloc_re = f"^(?:www.)?{netloc_re}$"
            self.netloc_re = re.compile(netloc_re, re.IGNORECASE)
        if ppath:
            self.path_re = self._path_or_fragment_re(ppath)
        if pfragment:
            self.fragment_re = self._path_or_fragment_re(pfragment)
        if pquery:
            pkvs = parse_qs(pquery, keep_blank_values=True)
            query_re_dict = {}
            for pparam, values in pkvs.items():
                pparam = pparam.lower()
                if "*" in pparam:
                    warnings.warn(
                        f"Wildcard expansion is only allowed for the values in the query parameter. Pattern: '{self.pattern}'",
                        SyntaxWarning,
                    )
                    pparam = pparam.replace("*", "")
                if not pparam:
                    continue
                param_re = fr"^(?:{'|'.join([_wildcard_re_escape(value) for value in values])})$"
                query_re_dict[pparam] = re.compile(param_re, re.IGNORECASE)
            self.query_re_dict = query_re_dict or None

    def match(self, url: str) -> bool:
        """
        Return True if the url matches the pattern.
        """
        parsed = _urlparse(url)
        if self.parsed.scheme:
            if parsed.scheme != self.parsed.scheme:
                return False
        if self.netloc_re:
            if not self.netloc_re.match(parsed.netloc):
                return False
        if self.path_re:
            if not self.path_re.match(parsed.path):
                return False
        if self.fragment_re:
            if not self.fragment_re.match(parsed.fragment):
                return False
        if self.query_re_dict:
            kvs = parse_qs(parsed.query, keep_blank_values=True)
            kvs = {k.lower(): v for k, v in kvs.items()}
            # All params must be present in the URL
            for param, param_re in self.query_re_dict.items():
                if param not in kvs:
                    return False
                if not any(param_re.match(value) for value in (kvs[param])):
                    return False
        return True

    @staticmethod
    def _path_or_fragment_re(path_or_fragment: str) -> Pattern:
        """Wildcard expansion + end of line character"""
        re_str = _wildcard_re_escape(path_or_fragment)
        if re_str.endswith(r"\|"):
            # case where the match must be exact
            re_str = re_str[:-2]
        else:
            re_str += r".*"
        re_str = f"^{re_str}$"
        return re.compile(re_str, re.IGNORECASE)
