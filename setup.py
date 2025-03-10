import os
from setuptools import setup, find_packages

# Read the contents of the README file
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="simpleaihelper",
    version="0.1.0",
    author="AI Kit Developer",
    author_email="aixiasang@163.com",
    description="A high-performance wrapper for OpenAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aixiasang/simpleaihelper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "openai>=1.0.0",
    ],
) 