"""
Example of usage of the URLMatcher library
"""
import dataclasses
import random
import time
from collections import Counter

from url_matcher import Patterns, URLMatcher
from url_matcher.matcher import IncludePatternsWithoutDomainError

matcher = URLMatcher()

# Let's add a rule for books to scrape product
patterns = Patterns(include=("books.toscrape.com/catalogue/",), exclude=("/catalogue/category/",))
matcher.add_or_update("books product", patterns)

# Now a rule for product list in books to scrape
patterns = Patterns(
    include=("books.toscrape.com/catalogue/category/", "books.toscrape.com/|", "books.toscrape.com/index.html|")
)
matcher.add_or_update("books productList", patterns)


# Let's try it

url = "https://books.toscrape.com/catalogue/soumission_998/index.html"
assert matcher.match(url) == "books product"

url = "https://books.toscrape.com/catalogue/category/books/fiction_10/index.html"
assert matcher.match(url) == "books productList"

url = "https://amazon.com"
assert not matcher.match(url)

# Adding a pattern without domain fails

try:
    matcher.add_or_update("won't work", Patterns(("/path",)))
    raise AssertionError
except IncludePatternsWithoutDomainError:
    ...

# But the empty pattern works. It matches anything

assert URLMatcher({"Anything": Patterns(("",))}).match("http://anything")

# Now let's see that priorities are working. They are applied only if several
# rules match the URL.

patterns = Patterns(("priority.com",))
matcher.add_or_update("low priority", dataclasses.replace(patterns, priority=200))
matcher.add_or_update("high priority", dataclasses.replace(patterns, priority=300))
assert matcher.match("http://priority.com") == "high priority"

# Let's invert the priorities

matcher.add_or_update("low priority", dataclasses.replace(patterns, priority=300))
matcher.add_or_update("high priority", dataclasses.replace(patterns, priority=200))
assert matcher.match("http://priority.com") == "low priority"

# Let's check the speed creating patterns for many domains and matching
# urls for these domains.


def add_patterns(domain):
    patterns = Patterns(include=[f"{domain}/catalogue/?param=book"], exclude=["/catalogue/category/"])
    matcher.add_or_update(f"{domain} product", patterns)

    patterns = Patterns(include=[f"{domain}/catalogue/category/?param=book_list", f"{domain}/", f"{domain}/index.html"])
    matcher.add_or_update(f"{domain} productList", patterns)


N_DOMAINS = 500
N_URLS = 300

URLS = [
    "https://books.toscrape.com/catalogue/soumission_998/index.html?param=book&p1=23&p2=45",
    "https://books.toscrape.com/catalogue/category/books/fiction_10/index.html?param=book_list&p5=23&p6=45",
]

# Adding the patterns
for idx in range(N_DOMAINS):
    add_patterns(idx)

urls = []
for _ in range(N_URLS):
    url = random.choice(URLS)
    domain = random.randint(0, N_DOMAINS - 1)
    url = url.replace("books.toscrape.com", f"{domain}")
    urls.append((domain, url))

# Let's try to match the urls
start = time.perf_counter()
counter: Counter = Counter()
for domain, url in urls:
    match = matcher.match(url)
    counter[bool(match)] += 1
    assert match and f"{domain}" in match
end = time.perf_counter()

# It took in my machine ~ 0.04 millis per URL
print(f"{((end-start)/N_URLS)*1000:.3f} milliseconds per URL. Total {end-start} seconds to match {N_URLS} URLs")

print("Everything worked fine!")
