import os

from setuptools import find_packages, setup

NAME = "url-matcher"


def get_version():
    about = {}
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, NAME.replace("-", "_"), "__version__.py")) as f:
        exec(f.read(), about)
    return about["__version__"]


setup(
    name=NAME,
    version=get_version(),
    description="URL matching rules library to connect URLs with resources",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    author="Zyte Group Ltd",
    author_email="info@zyte.com",
    url="https://github.com/zytedata/url-matcher",
    packages=find_packages(
        exclude=[
            "tests",
        ]
    ),
    package_data={
        "url_matcher": ["py.typed"],
    },
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "tldextract>=1.2",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
