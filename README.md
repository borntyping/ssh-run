ssh-run
=======

A tiny script for running a command using your current directory on a remote
server using ssh.

Usage
-----

	ssh-run [-h] [-w workspace] host command

Run `command` on `host`, using `rsync` to copy the current directory to and from the remote server (in `~/.ssh-run` by default, or the path set by `-w`).

Author
------

`ssh-run` was written by [Sam Clements](https://github.com/borntyping).
