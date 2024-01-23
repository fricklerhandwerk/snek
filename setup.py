#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="snek",
    version="0.0.0",
    summary="a plain and simple snake implementation",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "snek = snek.main:main"
        ]
    },
)
