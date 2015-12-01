#!/usr/bin/env python
"""Packaging, distributing, and installing the ConsumerSurveys lib."""

import setuptools

# To debug, set DISTUTILS_DEBUG env var to anything.
setuptools.setup(
    name="GoogleConsumerSurveys",
    version="0.0.0.3",
    packages=setuptools.find_packages(),
    author="Google Consumer Surveys",
    author_email="gcs-api-trusted-testers@googlegroups.com",
    keywords="google consumer surveys api client",
    url="https://github.com/google/consumer-surveys",
    license="Apache License 2.0",
    description=("Client API for Google Consumer Surveys API"),
    zip_safe=True,
    include_package_data=True,
    # Exclude these files from installation.
    exclude_package_data={"": ["README"]},
    install_requires=[
      "google-api-python-client >= 1.4.2",
      ],
    extras_require={},
)
