ssh-run
=======

A tiny script for running a command using your current directory on a remote
server using ssh.

Usage
-----

	ssh-run [-h] [-w workspace] host command

Run `command` on `host`, placing a copy of the current directory in `workspace`
(which defaults to `~/.ssh-run`).

Author
------

`ssh-run` was written by `Sam Clements <https://github.com/borntyping>`_.
