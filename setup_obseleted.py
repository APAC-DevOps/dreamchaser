# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.md").read()
except IOError:
    long_description = ""

setup(
    name="Jenkins",
    version="0.1.0",
    description="A Jianhua Wu projet",
    long_description=long_description,
    long_description_content_type='text/markdown',

    author="Jianhua Wu",
    author_email="jianhua.wu@dreamchaser.one",
    url="https://dreamchaser.one",
    
    package_dir={"": "dreamchaser"},
    packages=find_packages(where="dreamchaser"),

    install_requires=[
        "aws-cdk-lib==2.0.0-rc.21",
        "constructs>=10.0.0,<11.0.0",
        "boto3>=1.18.35"
    ],
    python_requires=">=3.6",
    
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Dreamchasers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities"
    ]
)
