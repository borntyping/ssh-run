"""The main ssh-run command runner"""

import concurrent.futures
import getpass
import socket
import sys

import paramiko
import termcolor

import ssh_run.ssh


class LineBuffer(object):
    NEWLINE = bytes('\n', 'utf-8')

    def __init__(self):
        self._buffer = bytes()

    def recv(self, data):
        self._buffer += data
        while self.NEWLINE in self._buffer:
            line, self._buffer = self._buffer.split(self.NEWLINE, 1)
            yield line.decode(encoding='UTF-8').strip()


class SSHRunFormatter(object):
    DEFAULT_FORMAT = "[{host}] {message}"
    CHANNEL_COLORS = {
        'STDERR': 'yellow',
        'STDOUT': None
    }

    def __init__(self, hosts, message_format=DEFAULT_FORMAT):
        self.width = max(len(host) for host in hosts)
        self.message_format = message_format

    def _format(self, host, message, message_color):
        return self.message_format.format(
            host=termcolor.colored("{:{}}".format(host, self.width), 'cyan'),
            message=termcolor.colored(message, message_color))

    def output(self, host, channel, line):
        color = self.CHANNEL_COLORS.get(channel, None)
        print(self._format(host, channel + ': ' + line, color))

    def error(self, host, message):
        print(self._format(host, message, 'red'), file=sys.stderr)

    def announce(self, message, color='green', end='\n'):
        print(self._format('localhost', message, color), end=end)

    def announce_ask(self, message, color='green'):
        self.announce(message, color, end='')
        sys.stdout.flush()


class SSHRun(object):
    def __init__(self, command, hosts, max_workers=1, sudo_password=False):
        self.command = command
        self.hosts = hosts
        self.max_workers = max_workers
        self.sudo_password = sudo_password
        self.fmt = SSHRunFormatter(hosts=hosts)

    def announce(self):
        fmt = lambda m: m.format(self.command, ', '.join(self.hosts))
        if self._sudo_password:
            self.fmt.announce(fmt("Running '{}' using sudo on {}"), 'red')
        else:
            self.fmt.announce(fmt("Running '{}' on {}"), 'green')
        return self

    @property
    def sudo_password(self):
        if self._sudo_password is True:
            self.fmt.announce_ask("Sudo password: ")
            self.sudo_password = getpass.getpass('')
        return self._sudo_password

    @sudo_password.setter
    def sudo_password(self, sudo_password):
        self._sudo_password = sudo_password

    def run(self, host):
        """Manage a host/client for use in exec_command()"""
        client = ssh_run.ssh.SSHClient(sudo_password=self.sudo_password)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(host)
        except socket.error:
            self.fmt.error(host, "Failed to connect")
        else:
            self.exec_command(host, client)
        finally:
            client.close()

    def exec_command(self, host, client):
        """Run a command on a given host/client pair"""
        stdin, stdout, stderr = client.exec_command(self.command)

        stdout_buffer = LineBuffer()
        stderr_buffer = LineBuffer()

        while True:
            stdout_data = stdin.channel.recv(1024)
            for line in stdout_buffer.recv(stdout_data):
                self.fmt.output(host, 'STDOUT', line)

            stderr_data = stdin.channel.recv_stderr(1024)
            for line in stderr_buffer.recv(stderr_data):
                self.fmt.output(host, 'STDERR', line)

            if stdout_data == b'' and stderr_data == b'':
                break

    def main(self):
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers) as executor:
            return list(executor.map(self.run, self.hosts))
