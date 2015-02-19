#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-

"""Setup for streaming wikipedia edits"""

import glob
import os
import sys

import setuptools
from setuptools.command import test


class TestWithDiscovery(test.test):
    def finalize_options(self):
        super().finalize_options()
        self.test_args.insert(0, 'discover')
        # if tests are in same namespace as module, make sure
        # test_dir is on sys.path before setup loads module (before test discovery)
        test_path = os.path.abspath(self.test_suite)
        if os.path.exists(test_path):
            sys.path.insert(0, test_path)


SRC_PATH = os.path.join("src", "main", "python")
TEST_PATH = os.path.join("src", "test", "python")


def list_scripts():
    return glob.glob("scripts/*")


def main():
    assert (sys.version_info[0] >= 3 and sys.version_info[1] >= 4), \
        "Python version >= 3.4 required, got %r" % (sys.version_info,)

    version = "0.1"

    setuptools.setup(
        name="wikipedia-stream",
        description="Wikipedia Edit Stream",
        version=version,
        packages=setuptools.find_packages(SRC_PATH),
        namespace_packages=setuptools.find_packages(SRC_PATH),
        package_dir={
            "": SRC_PATH,
        },
        scripts=sorted(list_scripts()),

        install_requires=[
            "irc >= 11.0",
        ],

        test_suite=TEST_PATH,
        cmdclass={'test': TestWithDiscovery},

        # metadata for upload to PyPI
        author="WibiData engineers",
        author_email="eng@wibidata.com",
        license="Copyright (c) 2014, WibiData",
        url="http://wibidata.com",
    )


if __name__ == "__main__":
    main()