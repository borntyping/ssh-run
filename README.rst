ssh-run
=======

A tool for running commands on remote servers.

The original `ssh-run` was a small bash script for running a command using your
current directory on a remote server using SSH. This is being merged with a
Python script of the same name for running a command across multiple servers.

Installation
------------

Requires Python 3. The pycrypto library (required by paramiko) does not work
if installed globally on Python 3.4.

Author
------

Written by `Sam Clements <https://github.com/borntyping>`_ at
`DataSift <https://datasift.com/>`_.
