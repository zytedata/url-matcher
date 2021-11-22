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

.. image:: https://codecov.io/github/zytedata/url-matcher/coverage.svg?branch=master
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

License is BSD 3-clause.

* Documentation: https://url-matcher.readthedocs.io/
* Source code: https://github.com/zytedata/url-matcher
* Issue tracker: https://github.com/zytedata/url-matcher/issues


Developing
**********

Setup your local Python environment via:

1. ``pip install -r requirements-dev.txt``
2. ``pre-commit install``

Now everytime you perform a ``git commit``, these tools will run against the staged files:

* ``black``
* ``isort``
* ``flake8``
* ``mypy``

You can also directly invoke ``pre-commit run --all-files`` to run them without performing a commit.


Using sphinx-autobuild
~~~~~~~~~~~~~~~~~~~~~~

When working on documentation,it is convenient to use sphinx-autobuild.
First, run ``pip install -r docs/requirements.txt sphinx-autobuild``. Then run

::

    sphinx-autobuild docs docs/_build/html

and then open http://127.0.0.1:8000/ in a browser, to see the current version
of docs. A process would be running in a background, watching for docs changes;
when docs are changed, a build is started, and the web page
is refreshed automatically when the build is finished.
