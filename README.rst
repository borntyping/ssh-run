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

Run a shell command across multiple SSH servers in sequence.

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

Run a command on hosts matched by a chef search:

    knife search -i "chef_evironment:staging" 2>/dev/null | ssh-run -H - -- echo hello world

Start a shell for running multiple commands:

    ssh-run -h host1 -h host2

Requirements
------------

Runs on Python 2.6 and above, including Python 3.

Licence
-------

``ssh-run`` is licenced under the `MIT Licence <http://opensource.org/licenses/MIT>`_.

Author
------

Written by `Sam Clements <https://github.com/borntyping>`_ at
`DataSift <https://datasift.com/>`_.
