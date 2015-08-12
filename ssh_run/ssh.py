import os
import os.path

import pexpect
import termcolor

__all__ = ['SSHRun']


class Log:
    """A named log for use with pexpect.spawn() and SSHRun log messages."""

    def __init__(self, name, verbose):
        self.prompt = '[{}] '.format(termcolor.colored(name, 'blue'))
        self._verbose = verbose
        self.newline = True

    def write(self, data):
        """Write a stream to STDOUT, managing \\n and \\r correctly."""

        # Raise an exception if sudo prompts the user to retry their password.
        # This shouldn't be here but there's no other nice place to put it.
        if data.startswith('Sorry, try again.'):
            raise Exception("sudo password was incorrect")

        # Track newlines so that the prompt can be inserted in the right place.
        if self.newline:
            print(self.prompt, end='')
            self.newline = False

        if data.endswith('\n'):
            self.newline = True

        # Insert a prompt when the line is cleared
        data = data.replace('\r', '\r' + self.prompt)
        print(data, end='')

    def flush(self):
        pass

    def msg(self, message, color=None, always=False):
        """Write a log message as a colored output line"""
        if self._verbose or always:
            print(self.prompt + termcolor.colored(message, color))


class Spawn:
    def __init__(self, command, *arguments,
                 dry_run=False, log=None, timeout=None):
        self.command = command
        self.arguments = arguments

        self.dry_run = dry_run
        self.log = log
        self.timeout = timeout

    def __enter__(self):
        """Spawn the command."""
        self.msg('$ {} {}'.format(
            self.command, ' '.join(self.arguments)), 'cyan')
        if not self.dry_run:
            self.child = pexpect.spawnu(
                self.command, list(self.arguments),
                logfile=self.log, timeout=self.timeout)
            return self.child

    def __exit__(self, *exception):
        """Wait for the command to finish."""
        if not self.dry_run:
            self.child.expect(pexpect.EOF)
            self.child.close()
            if self.child.exitstatus == 0:
                self.msg("Command ran successfully. [0]", 'green')
            else:
                self.msg("Command failed to run! [{}]".format(
                    self.child.exitstatus), 'red', True)

    def __call__(self):
        with self:
            pass

    def msg(self, *args, **kwargs):
        """Write a message to the associated log if one is set"""
        if self.log is not None:
            self.log.msg(*args, **kwargs)


class SSHRun:
    """
    A runner that can be used to cconfigure and run commmands on remote hosts.
    """

    SUDO_PROMPT = 'ssh-run:'

    def __init__(self, *, dry_run=False, timeout=None, sudo=False,
                 sudo_password=None, verbose=False, workspace=False,
                 workspace_path=None):
        self.dry_run = dry_run
        self.timeout = timeout
        self.sudo = sudo
        self.sudo_password = sudo_password
        self.verbose = verbose
        self.workspace = workspace
        self.workspace_path = workspace_path

    def run(self, host, script):
        """
        Run a script or command on the host.

        Runs rsync before and after the SSH command if nesscary, and sends the
        sudo password when prompted. The logfile is disabled while sending too
        and from sudo so the prompt and password are not shown.
        """
        log = Log(host, verbose=self.verbose)

        if self.workspace:
            self.spawn(*self.prepare_rsync(
                src=self.workspace_path,
                dst=self.remote_workspace_path(host)), log=log)()

        with self.spawn(*self.prepare(host, script), log=log) as child:
            # Send the password when prompted by sudo.
            if self.sudo:
                child.logfile = None
                child.expect_exact(SSHRun.SUDO_PROMPT)
                child.sendline(self.sudo_password)
                child.expect_exact("\n")
                child.logfile = log

        if self.workspace:
            self.spawn(*self.prepare_rsync(
                src=self.remote_workspace_path(host),
                dst=self.workspace_path), log=log)()

    def prepare(self, host, script):
        """Prepare the SSH command to run."""
        command = [
            'ssh',
            '-o', 'BatchMode=yes',
            '-o', 'LogLevel=QUIET',
            '-t', host, '--'
        ]

        if self.sudo:
            command.extend(('sudo', '-p', SSHRun.SUDO_PROMPT, '--'))

        if self.workspace:
            script = ['cd', self.workspace_path, '&&'] + list(script)

        command.extend(('/bin/bash', '-c', '--'))
        command.append("\"{}\"".format(' '.join(script).replace('"', '\\"')))
        return command

    def spawn(self, *args, **kwargs):
        """Create a spawn instance using settings from this runner."""
        return Spawn(*args, dry_run=self.dry_run, **kwargs)

    def prepare_rsync(self, src, dst):
        """Prepare an rsync command."""
        rsync = ['rsync', '--archive', '--delete', '--update']
        if self.verbose:
            rsync.append('--verbose')
        rsync.extend((SSHRun.trailing(src), SSHRun.trailing(dst)))
        return rsync

    def remote_workspace_path(self, host):
        """A directory to use on the remote host for the workspace."""
        return '{}:~/.ssh-run_{}/'.format(
            host, os.path.basename(self.workspace_path))

    @staticmethod
    def trailing(path):
        if not path.endswith(os.path.sep):
            path += os.path.sep
        return path
