#!/usr/bin/env python3

import argparse
import getpass
import logging
import subprocess

import colorlog


class Runner(object):
    def __init__(self, command):
        self.command = command

    def execute(self, host):
        raise NotImplementedError


class SudoRunner(Runner):
    _sudo_prompt = 'ssh-run sudo prompt'

    def __init__(self, command):
        super().__init__(command)
        self.password = getpass.getpass('Sudo password: ')

    def _build_command(self, host):
        return [
            'ssh', '-q', '-tt', host, '--',
            'sudo -S -p "{}" -- {}'.format(self._sudo_prompt, self.command)
        ]

    def execute(self, host):
        command = self._build_command(host)

        log = logging.getLogger(host)
        log.info("Running '{}' on {}".format(self.command, host))

        try:
            proccess = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True, )
            stdout, _ = proccess.communicate(
                input=self.password + "\n",
                timeout=25)
            proccess.wait()
        except subprocess.TimeoutExpired:
            log.critical("Timed out: '{}' on {}".format(
                self.command, host))
        else:
            self.output(stdout)

            if proccess.returncode != 0:
                log.critical("Failed: '{}' on {}".format(
                    self.command, host))
            else:
                log.info("Completed '{}' on {}".format(
                    self.command, host))

            return proccess

    def output(self, stdout):
        for line in stdout.split('\n'):
            if self.password in line:
                continue
            if self._sudo_prompt in line:
                continue
            if not line:
                continue
            print('\t', line)


cli = argparse.ArgumentParser(add_help=False)
cli.add_argument('--help', action='help')

hosts = cli.add_mutually_exclusive_group(required=True)
hosts.add_argument('-h', '--host', action='append', dest='hosts')
hosts.add_argument('-H', '--hosts-file', type=argparse.FileType('r'))


cli.add_argument(
    '-s', '--sudo', action='store_const',
    const=SudoRunner, default=Runner, dest='runner')

cli.add_argument('command')


def parse_hosts_file(hosts_file):
    return (line.strip() for line in hosts_file.readlines())


def main():
    colorlog.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(log_color)s%(message)s%(reset)s')

    args = cli.parse_args()
    runner = args.runner(args.command)

    for host in (args.hosts or parse_hosts_file(args.hosts_file)):
        runner.execute(host)

if __name__ == '__main__':
    main()
