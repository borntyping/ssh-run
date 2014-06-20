"""Extensions to Paramiko so commands can be run using sudo"""

import paramiko


class SSHClient(paramiko.SSHClient):
    def __init__(self, *args, **kwargs):
        self.sudo_password = kwargs.pop('sudo_password', None)
        super().__init__(*args, **kwargs)

    def exec_command(self, command, *args, **kwargs):
        """Executes a command on the SSH server, optionally using sudo

        See paramiko.SSHClient.exec_command for a full explaination. This
        function adds the sudo parameter - when this parameter is True the
        command is run using sudo (using -S to send the password on STDIN).

        Flags:
            -k: Invalidate existing sudo timestamps
            -S: Read password from STDIN
            -p: Set the password prompt
        """
        if self.sudo_password:
            command = 'sudo -k -S -p "" -- bash -c "{}"'.format(command)

        stdin, stdout, stderr = super().exec_command(command, *args, **kwargs)

        if self.sudo_password:
            stdin.write(self.sudo_password + '\n')
            stdin.flush()

        return stdin, stdout, stderr
