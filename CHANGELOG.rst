=========
Changelog
=========

0.4.0 (2024-04-03)
------------------

* Added official support for Python 3.12.
* Added the :meth:`.URLMatcher.match_all` method that returns all matching
  identifiers.
* Adding a :class:`~.Patterns` instance with several patterns for the same
  domain to a :class:`~.URLMatcher` no longer creates multiple identical
  :class:`~.matcher.PatternsMatcher` instances.
* CI improvements.

0.3.0 (2023-09-21)
------------------

* Drop Python 3.7 support, make Python 3.11 support official.
* Support tldextract >= 3.6, make the requirement of tldextract >= 1.2
  explicit.

0.2.0 (2022-02-01)
------------------

* Update :class:`~.Patterns` to be **frozen** so instances can easily be
  deduped based on its hash uniqueness.
* Remove Python 3.6 support

0.1.0 (2021-11-19)
------------------

* Initial release
