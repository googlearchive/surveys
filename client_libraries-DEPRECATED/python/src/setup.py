#!/usr/bin/env python
"""Packaging, distributing, and installing the ConsumerSurveys lib."""

import setuptools

# To debug, set DISTUTILS_DEBUG env var to anything.
setuptools.setup(
    name="GoogleConsumerSurveys",
    version="0.0.0.4",
    packages=setuptools.find_packages(),
    author="Google Surveys",
    author_email="surveys-api@google.com",
    keywords="google surveys api client",
    url="https://developers.google.com/surveys",
    license="Apache License 2.0",
    description=(
      "Client API for Google Surveys API. NOTE: This package is deprecated and"
      " will be removed on December 1, 2016. Please use the Google API Python"
      " Client instead: https://developers.google.com/api-client-library/python/."
    ),
    zip_safe=True,
    include_package_data=True,
    # Exclude these files from installation.
    exclude_package_data={"": ["README"]},
    install_requires=[
      "google-api-python-client >= 1.4.2",
      ],
    extras_require={},
)
