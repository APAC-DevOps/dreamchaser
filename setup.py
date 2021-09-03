# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.rst").read()
except IOError:
    long_description = ""

setup(
    name="dreamchaser",
    version="0.1.0",
    description="A Jianhua WU's package provides an easy way for setting up Jenkins servers",
    long_description=long_description,
    long_description_content_type='text/markdown',

    author="Jianhua Wu",
    author_email="jianhua.wu@dreamchaser.one",
    url="https://dreamchaser.one",
    
    package_dir={"": "dreamchaser"},
    packages=find_packages(where="jenkins"),

    install_requires=[
        "aws-cdk.core==1.121.0",
    ],
    python_requires=">=3.6",
    
    classifiers=[
        "Development Status :: 1 - Alpha",

        "Intended Audience :: Dreamchasers",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        
        "License :: OSI Approved :: MIT License",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
        
        "Operating System :: OS Independent",
    ]
)
