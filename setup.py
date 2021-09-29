#!/usr/bin/env python
# Copyright (c) 2021 Andrew Leech <andrew@alelec.net>
#
from setuptools import setup, find_packages
from setuptools.command.sdist import sdist as _sdist

setup(
    name='outline-backup',
    author='Andrew Leech',
    author_email='andrew@alelec.net',
    url='https://gitlab.com/alelec/outline-backup',
    description='Tool to export data from outline wiki',
    packages=find_packages(),
    include_package_data=True,
    use_scm_version=True,
    setup_requires=['setuptools-scm'],
    install_requires=['setuptools-scm', 'requests', 'structured_config'],
    entry_points={
        'console_scripts': [
            'outline-backup = outline_backup.__init__:main',
        ]
    },
)
