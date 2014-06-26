"""ssh-run - A tool for running commands on remote servers"""

import io
import functools
import threading
import sys

import click
import pexpect


__version__ = '0.1.0-dev'


def parse_hosts(hostslist, hostsfile):
    hosts = []

    if hostslist:
        hosts.extend(hostslist)

    if hostsfile:
        hosts.extend(host.decode('utf-8').strip() for host in hostsfile)

    return hosts


class disable_logfile(object):
    def __init__(self, child):
        self.child = child
        self.logfile = None

    def __enter__(self):
        self.logfile = self.child.logfile
        self.child.logfile = None
        return self.child

    def __exit__(self, *exception):
        self.child.logfile = self.logfile


class Logfile(object):
    def __init__(self, host):
        self.host = host

    def readlines(self, data):
        buffer = io.StringIO(data.decode('utf-8'))
        return filter(None, map(str.strip, buffer.readlines()))

    def write(self, data):
        for line in self.readlines(data):
            print('[{}] {}'.format(self.host, line))

    def flush(self):
        pass


class SSHRunner(threading.Thread):
    def __init__(self, host, command):
        super().__init__()
        self.host = host
        self.command = command

    def run(self):
        ssh = pexpect.spawn('ssh', self.ssh_args + self.command_args)
        ssh.logfile = Logfile(self.host)
        self.login(ssh)
        ssh.expect(pexpect.EOF)

    @property
    def ssh_args(self):
        return [self.host, '-tq', '-o', 'BatchMode=yes', '--']

    @property
    def command_args(self):
        return [self.command]

    def login(self, ssh):
        pass


class SudoSSHRunner(SSHRunner):
    SUDO_PROMPT = 'ssh-run:'

    def __init__(self, host, command, password):
        super().__init__(host, command)
        self.password = password

    @property
    def command_args(self):
        return ['sudo', '-p', self.SUDO_PROMPT, '--', self.command]

    def login(self, ssh):
        with disable_logfile(ssh):
            ssh.expect(self.SUDO_PROMPT)
            ssh.sendline(self.password)


@click.command()
@click.option(
    '--host', '-h', 'hostslist', metavar='HOSTNAME', multiple=True,
    help='A single hostname. Can be used multiple times.')
@click.option(
    '--hosts', '-H', 'hostsfile', type=click.File('rb'),
    help='A file with one host per line. \'-\' reads from stdin.')
@click.option(
    '--sudo/--no-sudo', '-s',
    help='Run the command using sudo.')
@click.option(
    '--sudo-password',
    help='Sudo password, prompts if not set on command line and needed.')
@click.version_option(__version__)
@click.argument('command')
def main(hostslist, hostsfile, sudo, sudo_password, command):
    hosts = parse_hosts(hostslist, hostsfile)

    cls = SSHRunner

    if sudo:
        if not sudo_password:
            sudo_password = click.prompt('Sudo password', hide_input=True)
        cls = functools.partial(SudoSSHRunner, password=sudo_password)

    for host in hosts:
        cls(host, command).run()
