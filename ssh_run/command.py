"""Implements a command line entry point for ssh-run using argparse"""

import argparse

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
    'command',
    help='The command to run on the remote connection')
command.add_argument(
    'args', nargs=argparse.REMAINDER, metavar='...',
    help='Arguments to pass to the command')
command.add_argument(
    '-s', '--sudo', action='store_true', dest='sudo',
    help="Execute the command using sudo")
command.add_argument(
    '-S', '--no-sudo', action='store_false', dest='sudo',
    help="Do not edit the command and do not ask for a password")

hosts = parser.add_argument_group('Host options')
hosts.add_argument(
    '-H', '--host', action='append', dest='hosts', metavar='HOST',
    help="A host to run the command on - can be used multiple times")
hosts.add_argument(
    '-F', '--hosts', type=argparse.FileType('r'), metavar='HOSTS',
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


def main():
    args = parser.parse_args()

    print(args)
