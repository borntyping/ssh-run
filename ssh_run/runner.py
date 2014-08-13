"""ssh-run runner implementations"""

import io
import functools
import os
import os.path

import pexpect
import termcolor

__all__ = ['SSHRunner']


class Logfile(object):
    def __init__(self, host):
        self.host = host

    def print_line(self, line):
        host = termcolor.colored(self.host, 'cyan')
        print('[{}] {}'.format(host, line))

    def readlines(self, data):
        buffer = io.StringIO(data)
        return filter(None, map(str.rstrip, buffer.readlines()))

    def write(self, data):
        lines = io.StringIO(data).readlines()
        lines = filter(None, (line.rstrip() for line in lines))

        for line in lines:
            self.print_line(line.encode('utf-8'))

    def write_error(self, message):
        self.print_line(termcolor.colored(message, 'red'))

    def flush(self):
        pass


class Spawn(object):
    def __init__(self, command, args, host=None, verbose=False, timeout=300):
        self.command = command
        self.args = args
        self.host = host
        self.verbose = verbose
        self.timeout = timeout

    def __enter__(self):
        self.logfile = Logfile(self.host)
        if self.verbose:
            self.logfile.print_line(termcolor.colored('$ {} {}'.format(
                self.command, ' '.join(self.args)), 'grey', attrs=['bold']))
        self.child = pexpect.spawnu(
            self.command, self.args,
            logfile=self.logfile, timeout=self.timeout)
        return self.child

    def __exit__(self, *exception):
        self.child.expect(pexpect.EOF)
        self.child.close()
        if self.child.exitstatus != 0:
            self.child.logfile.write_error(
                'Failed to run command [{}]'.format(self.child.exitstatus))


class SSHRunner(object):
    SSH_OPTS = {
        'BatchMode': 'yes',
        'LogLevel': 'QUIET'
    }

    SUDO_PROMPT = u'ssh-run:'

    WORKSPACE = '~/.ssh-run-workspace'

    @classmethod
    def partial(cls, *args, **kwargs):
        return functools.partial(cls, *args, **kwargs)

    def __init__(self, host, command,
                 sudo=False, sudo_password=None,
                 workspace=False, verbose=False, timeout=300):
        self.host = host
        self.command = command
        self.sudo = sudo
        self.sudo_password = sudo_password
        self.workspace = workspace
        self.verbose = verbose
        self.timeout = timeout

    def run(self):
        if self.workspace:
            self.sync_workspace(self._local_workspace, self._remote_workspace)

        with self.spawn('ssh', self.args()) as ssh:
            if self.sudo:
                with self.disable_logfile(ssh):
                    ssh.expect(self.SUDO_PROMPT)
                    ssh.sendline(self.sudo_password)

        if self.workspace:
            self.sync_workspace(self._remote_workspace, self._local_workspace)

    def spawn(self, command, args):
        return Spawn(
            command, args, host=self.host,
            verbose=self.verbose, timeout=self.timeout)

    # SSH

    def args(self):
        return self.ssh_args() + self.command_args()

    def ssh_args(self):
        args = [self.host, '-t']
        args.extend(self.ssh_opts())
        args.append('--')
        return args

    def ssh_opts(self):
        for k, v in self.SSH_OPTS.items():
            yield '-o'
            yield '{}={}'.format(k, v)

    def command_args(self):
        command = self.command

        if self.workspace:
            command = 'cd {} && {}'.format(
                self._remote_workspace_path, command)

        command = 'bash -c -- "{}"'.format(command)

        if self.sudo:
            command = 'sudo -p "{}" -- {}'.format(self.SUDO_PROMPT, command)

        return [command]

    # Workspace

    def sync_workspace(self, src, dest):
        opts = ['--archive', '--delete', '--update']
        if self.verbose:
            opts.append('--verbose')
        with self.spawn('rsync', opts + [src, dest]):
            pass

    @property
    def _local_workspace(self):
        return './'

    @property
    def _remote_workspace(self):
        return '{}:{}'.format(self.host, self._remote_workspace_path)

    @property
    def _remote_workspace_path(self):
        return '/tmp/ssh-run-workspace_{}/'.format(
            os.path.basename(os.getcwd()))

    # Sudo

    class disable_logfile(object):
        """Context mangager to temporarily disable a Pexpect logfile"""

        def __init__(self, child):
            self.child = child
            self.logfile = None

        def __enter__(self):
            self.logfile = self.child.logfile
            self.child.logfile = None
            return self.child

        def __exit__(self, *exception):
            self.child.logfile = self.logfile
