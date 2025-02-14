from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="url-matcher",
    version="0.6.0",
    description="URL matching rules library to connect URLs with resources",
    long_description=Path("README.rst").read_text(encoding="utf-8"),
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
