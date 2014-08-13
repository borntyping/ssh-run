"""ssh-run command line interface"""

import click

import ssh_run
import ssh_run.runner


def parse_hosts(hostslist, hostsfile):
    hosts = []

    if hostslist:
        hosts.extend(hostslist)

    if hostsfile:
        hosts.extend(host.decode('utf-8').strip() for host in hostsfile)

    return hosts


def create_runner_class(sudo, sudo_password, workspace, verbose, timeout):
    if sudo and not sudo_password:
        sudo_password = click.prompt('Sudo password', hide_input=True)
    return ssh_run.runner.SSHRunner.partial(
        sudo=sudo, sudo_password=sudo_password,
        workspace=workspace, verbose=verbose, timeout=timeout)


@click.command()
@click.option(
    '--host', '-h', 'hosts_l', metavar='HOSTNAME', multiple=True,
    help='A single hostname. Can be used multiple times.')
@click.option(
    '--hosts', '-H', 'hosts_f', type=click.File('rb'),
    help='A file with one host per line. \'-\' reads from stdin.')
@click.option(
    '--timeout', '-t', type=click.INT, default=300,
    help='Timeout in seconds.')
@click.option(
    '--sudo/--no-sudo', '-s', default=False,
    help='Run the command using sudo.')
@click.option(
    '--sudo-password',
    help='Sudo password, prompts if not set on command line and needed.')
@click.option(
    '--workspace/--no-workspace', '-w', default=False,
    help='Copy the current workspace to a remote host.')
@click.option(
    '--verbose/--no-verbose', '-v', default=False,
    help='Output commands before running them.')
@click.version_option(ssh_run.__version__, '--version', '-V')
@click.argument('command', nargs=-1, required=True)
def main(
        hosts_l, hosts_f, timeout, sudo, sudo_password, workspace, verbose,
        command):
    runner = create_runner_class(
        sudo, sudo_password, workspace, verbose, timeout)
    command = ' '.join(command)
    for host in parse_hosts(hosts_l, hosts_f):
        runner(host, command).run()
