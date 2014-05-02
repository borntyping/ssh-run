"""Classes for running commands via ssh"""

import paramiko


class Runner(object):
    @classmethod
    def create(cls, command, *args, **kwargs):
        if command.startswith('sudo '):
            cls = SudoRunner
            command = command[5:]
        return cls(command, *args, **kwargs)

    def __init__(self, command):
        self.command = command


class SudoRunner(Runner):
    pass
