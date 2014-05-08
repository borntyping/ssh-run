"""Implements a command line entry point for ssh-run using argparse"""

import argparse
import concurrent.futures
import getpass
import socket

import paramiko
import termcolor

import ssh_run
import ssh_run.ssh

parser = argparse.ArgumentParser()
parser.add_argument(
    '-v', '--version', action='version',
    version='ssh-run {}'.format(ssh_run.__version__))

command = parser.add_argument_group(
    "Command options",
    "If the command starts with 'sudo', the --sudo flag will be set on by"
    "default. You can use the --no-sudo flag to prevent this.")
command.add_argument(
    'command', metavar='command', nargs=argparse.REMAINDER,
    help='The command to run on the remote connection')

sudo = command.add_mutually_exclusive_group()
sudo.add_argument(
    '-s', '--sudo', action='store_true', dest='sudo',
    help="Execute the command using sudo")
sudo.add_argument(
    '-S', '--no-sudo', action='store_false', dest='sudo',
    help="Do not edit the command and do not ask for a password")
sudo.add_argument(
    '-P', '--sudo-password-file', type=argparse.FileType('r'),
    help="Execute using sudo and read the password from a file")

hosts = parser.add_argument_group('Host options')
hosts.add_argument(
    '-H', '--host', action='append', dest='hosts', metavar='HOST', default=[],
    help="A host to run the command on - can be used multiple times")
hosts.add_argument(
    '-F', '--hostfile', action='append', dest='hostfiles', metavar='PATH',
    default=[], type=argparse.FileType('r'),
    help="A file containing a list of hosts to run the command on")

# workspace = parser.add_argument_group(
#     'Workspace options',
#     '%(prog)s can sync the current directory with the remote host before and '
#     'after running the command. By default, it will create directories in '
#     '~/.ssh-run/$name, where $name is the name of the current directory.')
# workspace = workspace.add_mutually_exclusive_group()
# workspace.add_argument(
#     '-w', '--copy-workspace', action='store_true', dest='workspace',
#     help="Copy the current workspace to ~/.ssh-run/{dirname}")
# workspace.add_argument(
#     '-W', '--copy-workspace-to', dest='workspace', metavar='PATH',
#     help="Copy the current workspace to a specified directory")


class SSHRun(object):
    class Formatter(object):
        DEFAULT_FORMAT = "[{host}] {message}"
        CHANNEL_COLORS = {
            'STDERR': 'yellow',
            'STDOUT': 'white'
        }

        def __init__(self, hosts, message_format=DEFAULT_FORMAT):
            self.width = max(len(host) for host in hosts)
            self.message_format = message_format

        def _message(self, host, message, color=None):
            host = termcolor.colored("{:{}}".format(host, self.width), 'cyan')
            print(self.message_format.format(host=host, message=message))

        def output(self, host, channel, line):
            color = self.CHANNEL_COLORS.get(channel, None)
            message = termcolor.colored(channel + ': ' + line, color)
            self._message(host, message)

        def error(self, host, message):
            self._message(host, termcolor.colored(message, 'red'))

    def __init__(self, command, hosts, sudo_password=None):
        self.command = command
        self.hosts = hosts
        self.sudo_password = sudo_password

        self.fmt = self.Formatter(hosts=hosts)

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
        for channel, name in ((stdout, 'STDOUT'), (stderr, 'STDERR')):
            for line in channel.readlines():
                self.fmt.output(host, name, line.strip())

    def main(self):
        print("Running '{}' on {}".format(self.command, ', '.join(self.hosts)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            return list(executor.map(self.run, self.hosts))


def parse_command(args):
    return ' '.join(args.command)


def parse_hosts(args):
    hosts = list()
    hosts.extend(args.hosts)
    hosts.extend(h.strip() for f in args.hostfiles for h in f.readlines())
    return hosts


def parse_sudo(args):
    if args.sudo_password_file:
        return args.sudo_password_file.read().strip()
    elif args.sudo:
        return getpass.getpass('Sudo password:')
    return None


def main():
    args = parser.parse_args()

    SSHRun(
        command=parse_command(args),
        hosts=parse_hosts(args),
        sudo_password=parse_sudo(args)
    ).main()
