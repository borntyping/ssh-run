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


def create_runner_class(sudo, password):
    if sudo:
        password = password or click.prompt('Sudo password', hide_input=True)
        return ssh_run.runner.SudoSSHRunner.partial(password=password)
    return ssh_run.runner.SSHRunner


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
@click.version_option(ssh_run.__version__)
@click.argument('command')
def main(hostslist, hostsfile, sudo, sudo_password, command):
    runner = create_runner_class(sudo, sudo_password)
    for host in parse_hosts(hostslist, hostsfile):
        runner(host, command).run()
