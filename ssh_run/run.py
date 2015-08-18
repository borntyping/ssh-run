"""ssh-run command line interface"""

import os

import click
import keyring

import ssh_run
import ssh_run.ssh


def parse_hosts(hosts_list, hosts_file):
    hosts = []

    if hosts_list:
        hosts.extend(hosts_list)

    if hosts_file:
        hosts.extend(host.decode('utf-8').strip() for host in hosts_file)

    if not hosts:
        raise Exception('No hosts provided')

    return hosts


def get_sudo_password(password, keyring_context):
    """
    Prompt the user for a password to use with sudo.

    Priority: --sudo-password, --keyring, prompt.
    """

    # First try getting a password from the keyring.
    if not password and keyring_context:
        password = keyring.get_password('sshrun', keyring_context)

    # Then prompt for input if there was no password.
    if not password:
        password = click.prompt(
            '[sudo] password for remote hosts', hide_input=True, err=True)

        # Store the password if we are using a keyring.
        if keyring_context:
            keyring.set_password('sshrun', keyring_context, password)

    return password


@click.command(context_settings={'auto_envvar_prefix': 'SSH_RUN'})
@click.option(
    '--host', '-h', 'hosts_list', metavar='HOSTNAME', multiple=True,
    help='A single hostname. Can be used multiple times.')
@click.option(
    '--hosts', '-H', 'hosts_file', type=click.File('rb'),
    help='A file with one host per line.')
@click.option(
    '--dry-run', '-n', is_flag=True,
    help='Don\'t run any commands.')
@click.option(
    '--sudo', '-s', is_flag=True, default=False,
    help='Run the command using sudo.')
@click.option(
    '--sudo-password', '-p',
    help='Password for --sudo. Prompts if not set.')
@click.option(
    '--sudo-keyring', '-k', 'sudo_keyring', metavar='CONTEXT',
    help='Use the system keyring to store the password.')
@click.option(
    '--timeout', '-t', type=click.INT, default=300,
    help='Command timeout in seconds.')
@click.option(
    '--workspace', '-w', is_flag=True, default=False,
    help='Copy the current workspace to a remote host.')
@click.option(
    '--workspace-path', '-W',
    type=click.Path(exists=True), default=os.getcwd(),
    help='The directory to use as the workspace.')
@click.option(
    '--verbose/--no-verbose', '-v', default=False,
    help='Output commands before running them.')
@click.version_option(ssh_run.__version__, '--version', '-V')
@click.argument('command', nargs=-1)
def main(hosts_list, hosts_file, dry_run, timeout, sudo, sudo_password,
         sudo_keyring, workspace, workspace_path, verbose, command):
    """
    Run a command across multiple hosts in sequence.

    The --sudo and --sudo-password options allow the commands to be run with
    sudo, prompting for a password once and then sending that to the remote
    host when prompted.

    The --workspace and --workspace-path options will sync the current
    directory or a specificed directory with the remote host before and after
    running the command. Workspaces are stored in ~/.ssh-run_<basename> on the
    remote host.

    If no command is given, an interactive shell is started which will run the
    input commands on each host.
    """

    # Create a runner with the settings used on every host.
    runner = ssh_run.ssh.SSHRun(
        parse_hosts(hosts_list, hosts_file), dry_run=dry_run, sudo=sudo,
        sudo_password=get_sudo_password(sudo_password, sudo_keyring),
        timeout=timeout, verbose=verbose, workspace=workspace,
        workspace_path=workspace_path)

    # Run the command or start a shell for running multiple commands.
    runner.run(command) if command else runner.shell()
