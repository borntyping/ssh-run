"""Extensions to Paramiko so commands can be run using sudo"""

import getpass

import paramiko


class SSHClient(paramiko.SSHClient):
    use_sudo = False
    sudo_password = None

    def use_sudo(self, password=None):
        self.use_sudo = True
        self.sudo_password = password or getpass.getpass('Sudo password:')

    def exec_command(self, command, *args, **kwargs):
        """Executes a command on the SSH server, optionally using sudo

        See paramiko.SSHClient.exec_command for a full explaination. This
        function adds the sudo parameter - when this parameter is True the
        command is run using sudo (using -S to send the password on STDIN).
        """
        if self.use_sudo:
            if self.sudo_password is None:
                raise paramiko.ssh_exception.PasswordRequiredException(
                    'No sudo password has been set! Call set_sudo_password()')
            command = 'sudo -S -p "" -- ' + command

        stdin, stdout, stderr = super().exec_command(command, *args, **kwargs)

        if self.use_sudo:
            stdin.write(self.sudo_password + '\n')
            stdin.flush()

        return stdin, stdout, stderr
