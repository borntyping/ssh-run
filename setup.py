#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name='ssh-run',
    version='0.5.0',

    author="Sam Clements",
    author_email="sam@borntyping.co.uk",

    url="https://github.com/borntyping/ssh-run",
    description="A tool for running commands on remote servers",
    long_description=open('README.rst').read(),

    packages=['ssh_run'],
    install_requires=[
        'click',
        'pexpect',
        'termcolor'
    ],

    entry_points={
        'console_scripts': [
            'ssh-run = ssh_run.cli:main'
        ]
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ],
)
