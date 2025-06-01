__author__ = 'Duc Bui'

import setuptools
from pathlib import Path

long_description = Path('README.md').read_text()

setuptools.setup(
    name="consent-project",
    version="0.0.2",
    author="Duc Bui",
    author_email="ducbui@umich.edu",
    description="User cookie preference analysis",
    license='Apache License 2.0',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/ducalpha/consent_project",
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.8',
)
