"""Implements a command line entry point for ssh-run using argparse"""

import argparse
import concurrent.futures
import getpass

import paramiko

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


class SSHRun(object):
    def __init__(self, command, sudo_password=None):
        self.command = command
        self.sudo_password = sudo_password

    def run(self, host):
        ssh = ssh_run.ssh.SSHClient(sudo_password=self.sudo_password)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host)

        stdin, stdout, stderr = ssh.exec_command(self.command)

        for channel, name in ((stdout, 'STDOUT'), (stderr, 'STDERR')):
            for line in channel.readlines():
                print("[{:30}] {}: {}".format(host, name, line.strip()))


def main():
    args = parser.parse_args()
    args.hosts.extend(parse_hostfiles(args.hostfiles))
    args.command = ' '.join(args.command)

    print("Running '{}' on {}".format(args.command, ', '.join(args.hosts)))

    if args.sudo_password_file:
        password = args.sudo_password_file.read().strip()
    elif args.sudo:
        password = getpass.getpass('Sudo password:')
    else:
        password = None

    ssh_run = SSHRun(args.command, password)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(ssh_run.run, args.hosts))
