===========
url-matcher
===========

.. image:: https://img.shields.io/pypi/v/url-matcher.svg
   :target: https://pypi.python.org/pypi/url-matcher
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/url-matcher.svg
   :target: https://pypi.python.org/pypi/url-matcher
   :alt: Supported Python Versions

.. image:: https://github.com/zytedata/url-matcher/workflows/tox/badge.svg
   :target: https://github.com/zytedata/url-matcher/actions
   :alt: Build Status

.. image:: https://codecov.io/github/zytedata/url-matcher/coverage.svg?branch=main
   :target: https://codecov.io/gh/zytedata/url-matcher
   :alt: Coverage report


URL matching library that relates URLs with resources. Rules are defined using
simple pattern definitions. It is simpler and faster than using regular expressions
if the rules involves many domains.

To illustrate it with an example, imagine that you have several proxy servers and
you want to route requests to the right one. You could define the following rules:

* ``site1.com`` →︎ ``us_proxy``
* ``site2.com/uk`` →︎ ``uk_proxy``
* ``site2.com/ie`` →︎ ``ie_proxy``

All URLs from ``site1.com`` should use the US proxy. The situation for ``site2.com`` URLs are
different: if the path starts with ``/uk``, then use the UK proxy, otherwise use the IE proxy.
This library allows to create a matcher that can be used to match URLs with the right proxy
using these rules.

Have a look to https://github.com/zytedata/url-matcher/blob/main/url_matcher/example.py
for an example of usage.

The following files are useful to understand the pattern, the set of patterns and
how they behave:

* https://github.com/zytedata/url-matcher/blob/main/tests/fixtures/single_patterns.json
* https://github.com/zytedata/url-matcher/blob/main/tests/fixtures/patterns.json

The full documentation can be found at https://url-matcher.readthedocs.io/

License is Apache 2.0.

* Documentation: https://url-matcher.readthedocs.io/
* Source code: https://github.com/zytedata/url-matcher
* Issue tracker: https://github.com/zytedata/url-matcher/issues


Developing
**********

We use tox_ to run tests, type checks and linters:

* ``tox`` runs the tests on every supported Python version, the type checks
  (mypy) and the documentation build.
* ``tox -e py`` runs the tests on your current Python version.
* ``tox -e pre-commit`` runs the linters and formatters configured in
  ``.pre-commit-config.yaml``.

To also run the linters and formatters against the staged files on every
``git commit``, install pre-commit_ and its git hook::

    pip install pre-commit
    pre-commit install

.. _pre-commit: https://pre-commit.com
.. _tox: https://tox.wiki


Using sphinx-autobuild
~~~~~~~~~~~~~~~~~~~~~~

When working on documentation, it is convenient to use sphinx-autobuild.
First, run ``pip install -r docs/requirements.txt sphinx-autobuild``. Then run

::

    sphinx-autobuild docs docs/_build/html

and then open http://127.0.0.1:8000/ in a browser, to see the current version
of docs. A process would be running in a background, watching for docs changes;
when docs are changed, a build is started, and the web page
is refreshed automatically when the build is finished.
