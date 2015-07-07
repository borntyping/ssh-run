ssh-run
=======

.. image:: https://img.shields.io/pypi/v/ssh-run.svg
    :target: https://warehouse.python.org/project/ssh-run/
    :alt: ssh-run on PyPI

.. image:: https://img.shields.io/pypi/l/ssh-run.svg
    :target: https://warehouse.python.org/project/ssh-run/
    :alt: ssh-run on PyPI

.. image:: https://img.shields.io/github/issues/borntyping/ssh-run.svg?style=flat-square
    :target: https://github.com/borntyping/ssh-run/issues
    :alt: GitHub issues for ssh-run

|

A tool for running commands on remote servers.

Installation
------------

    pip install ssh-run

Usage
-----

Show usage information with:

    ssh-run --help

Examples
--------

Run a command on a single remote host:

    ssh-run -h example.com -- echo hello world

Run a command on multiple remote hosts:

    cat hosts | ssh-run -H - -- echo hello world

Requirements
------------

Runs on Python 3, *may* work on Python 2.

Licence
-------

``ssh-run`` is licenced under the `MIT Licence <http://opensource.org/licenses/MIT>`_.

Author
------

Written by `Sam Clements <https://github.com/borntyping>`_ at
`DataSift <https://datasift.com/>`_.
