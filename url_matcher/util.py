from functools import lru_cache
from urllib.parse import urlparse

from tldextract import tldextract


@lru_cache(100)
def get_domain(url: str) -> str:
    """
    Return the domain without any subdomain

    >>> get_domain("http://blog.example.com")
    'example.com'
    >>> get_domain("http://www.example.com")
    'example.com'
    >>> get_domain("http://deeper.blog.example.co.uk")
    'example.co.uk'
    >>> get_domain("http://127.0.0.1")
    '127.0.0.1'
    """
    return ".".join(el for el in tldextract.extract(url)[-2:] if el)


def is_absolute(url: str) -> bool:
    return bool(urlparse(url).netloc)
