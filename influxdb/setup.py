#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-

"""Setup for streaming wikipedia edits"""

import glob
import os
import sys

import setuptools
from setuptools.command import test

def list_scripts():
    return glob.glob("scripts/*")


def main():
    assert (sys.version_info[0] >= 3 and sys.version_info[1] >= 4), \
        "Python version >= 3.4 required, got %r" % (sys.version_info,)

    version = "0.1"

    setuptools.setup(
        name="influxdb-tests",
        description="Scripts for testing influxdb",
        version=version,
        scripts=sorted(list_scripts()),

        install_requires=[
            "wikipedia-stream >= 0.1",
            "influxdb >= 0.3.0"
        ],

        # metadata for upload to PyPI
        author="WibiData engineers",
        author_email="eng@wibidata.com",
        license="Copyright (c) 2014, WibiData",
        url="http://wibidata.com",
    )


if __name__ == "__main__":
    main()