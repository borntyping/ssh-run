"""Implements a command line entry point for ssh-run using argparse"""

import argparse
import getpass

import paramiko

import ssh_run
import ssh_run.runner

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
command.add_argument(
    '-s', '--sudo', action='store_true', dest='sudo',
    help="Execute the command using sudo")
command.add_argument(
    '-S', '--no-sudo', action='store_false', dest='sudo',
    help="Do not edit the command and do not ask for a password")

hosts = parser.add_argument_group('Host options')
hosts.add_argument(
    '-H', '--host', action='append', dest='hosts', metavar='HOST', default=[],
    help="A host to run the command on - can be used multiple times")
hosts.add_argument(
    '-F', '--hostfile', action='append', dest='hostfiles', metavar='PATH',
    type=argparse.FileType('r'),
    help="A file containing a list of hosts to run the command on")

workspace = parser.add_argument_group(
    'Workspace options',
    '%(prog)s can sync the current directory with the remote host before and '
    'after running the command. By default, it will create directories in '
    '~/.ssh-run/$name, where $name is the name of the current directory.')

workspace = workspace.add_mutually_exclusive_group()
workspace.add_argument(
    '-w', '--copy-workspace', action='store_true', dest='workspace',
    help="Copy the current workspace to ~/.ssh-run/{dirname}")
workspace.add_argument(
    '-W', '--copy-workspace-to', dest='workspace', metavar='PATH',
    help="Copy the current workspace to a specified directory")


def parse_hostfiles(hostfiles):
    return [h.strip() for hosts in hostfiles for h in hosts.readlines()]


class ExtendedSSHClient(paramiko.SSHClient):
    def exec_sudo_command(
        self, command, bufsize=-1, timeout=None, get_pty=False, password=None):
        """Executes a command on the SSH server using sudo"""
        command = 'sudo -S -p "" "{}"'.format(command)
        stdin, stdout, stderr = self.exec_command(
            command, bufsize=bufsize, timeout=timeout, get_pty=get_pty)

        # Send the password to sudo's STDIN
        stdin.write(password)
        stdin.flush()

        return stdin, stdout, stderr


def main():
    args = parser.parse_args()

    hosts = list()
    hosts.extend(args.hosts)
    hosts.extend(parse_hostfiles(args.hostfiles))

    command = ' '.join(args.command)
    password = open('pass', 'r').read()

    print("Running '{}' on {}".format(command, ', '.join(hosts)))

    ssh = ExtendedSSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for host in hosts:
        ssh.connect(host)

        if args.sudo:
            values = ssh.exec_sudo_command(command, password=password)
        else:
            values = ssh.exec_command(command)

        stdin, stdout, stderr = values

        for channel, channel_name in ((stdout, 'STDOUT'), (stderr, 'STDERR')):
            content = channel.read().strip()
            if content:
                print("[{:30}] {}: {}".format(host, channel_name, content))
