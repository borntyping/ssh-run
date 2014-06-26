"""ssh-run runner implementations"""

import io
import functools

import pexpect
import termcolor

__all__ = ['SSHRunner', 'SudoSSHRunner']


class Logfile(object):
    def __init__(self, host):
        self.host = host

    def print_line(self, line):
        print('[{}] {}'.format(self.host, line))

    def readlines(self, data):
        buffer = io.StringIO(data)
        return filter(None, map(str.strip, buffer.readlines()))

    def write(self, data):
        lines = io.StringIO(data).readlines()
        lines = filter(None, map(str.strip, lines))

        for line in lines:
            self.print_line(line)

    def write_error(self, message):
        self.print_line(termcolor.colored(message, 'red'))

    def flush(self):
        pass


class SSHRunner(object):
    SSH_OPTS = {
        'BatchMode': 'yes',
        'LogLevel': 'QUIET'
    }

    @classmethod
    def partial(cls, *args, **kwargs):
        return functools.partial(cls, *args, **kwargs)

    def __init__(self, host, command):
        super().__init__()
        self.host = host
        self.command = command

    def run(self):
        ssh = pexpect.spawnu('ssh', self.ssh_args() + self.command_args())
        ssh.logfile = Logfile(self.host)
        self.on_login(ssh)
        ssh.expect(pexpect.EOF)
        ssh.close()
        self.on_exit(ssh)

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
        return [self.command]

    def on_login(self, ssh):
        pass

    def on_exit(self, ssh):
        if ssh.exitstatus != 0:
            ssh.logfile.write_error(
                'Failed to run command [{}]'.format(ssh.exitstatus))


class SudoSSHRunner(SSHRunner):
    SUDO_PROMPT = 'ssh-run:'

    def __init__(self, host, command, password):
        super().__init__(host, command)
        self.password = password

    def command_args(self):
        return ['sudo', '-p', self.SUDO_PROMPT, '--', self.command]

    def on_login(self, ssh):
        with self.disable_logfile(ssh):
            ssh.expect(self.SUDO_PROMPT)
            ssh.sendline(self.password)

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
