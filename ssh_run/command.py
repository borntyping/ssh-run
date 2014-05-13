"""Implements a command line entry point for ssh-run using argparse"""

import argparse
import getpass

import ssh_run
import ssh_run.ssh
import ssh_run.run

parser = argparse.ArgumentParser()
parser.add_argument(
    '-v', '--version', action='version',
    version='ssh-run {}'.format(ssh_run.__version__))

command = parser.add_argument_group(
    "Command options",
    "If the command starts with 'sudo', the --sudo flag will be set on by"
    "default. You can use the --no-sudo flag to prevent this.")
command.add_argument(
    '-w', '--workers', type=int, default=1,
    help="The number of worker threads to use (default: 1)")
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
#     '%(prog)s can sync the current directory with the remote host before and'
#     'after running the command. By default, it will create directories in '
#     '~/.ssh-run/$name, where $name is the name of the current directory.')
# workspace = workspace.add_mutually_exclusive_group()
# workspace.add_argument(
#     '-w', '--copy-workspace', action='store_true', dest='workspace',
#     help="Copy the current workspace to ~/.ssh-run/{dirname}")
# workspace.add_argument(
#     '-W', '--copy-workspace-to', dest='workspace', metavar='PATH',
#     help="Copy the current workspace to a specified directory")


def parse_command(command):
    if not command:
        parser.error('A command must be provided')
    return ' '.join(command)


def parse_hosts(hosts, hostfiles):
    hosts = list()
    hosts.extend(hosts)
    hosts.extend(h.strip() for f in hostfiles for h in f.readlines())

    if not hosts:
        parser.error('No hosts were provided')

    return hosts


def parse_sudo(sudo, sudo_password_file):
    if sudo_password_file:
        return sudo_password_file.read().strip()
    else:
        return sudo


def main():
    args = parser.parse_args()

    ssh_run.run.SSHRun(
        parse_command(args.command),
        parse_hosts(args.hosts, args.hostfiles),
        args.workers,
        parse_sudo(args.sudo, args.sudo_password_file)
    ).announce().main()
