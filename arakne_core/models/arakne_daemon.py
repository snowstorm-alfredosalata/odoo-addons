# $$LICENSE_BRIEF$$

import io
import base64
import paramiko

from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend

from odoo import models, fields, api, _

# TODO: Implement this


class ArakneDaemon(models.Model):
    _description = """
    Allows mapping workcenters to a certain plant.
    Used mainly for grouping purposes on reports.
    """
    _name = 'arakne.daemon'

    name = fields.Char("Name", required=True)

    webapi_address = fields.Char("WebApi Address", required=True)

    ssh_address = fields.Char("Host Address")
    ssh_port = fields.Integer("Host Port")
    ssh_user = fields.Char("Host User")
    ssh_password = fields.Char("Host Password")

    def button_ssh_check(self):
        ssh = paramiko.SSHClient()

        # Automatically add the server's host key (this might not be secure in all cases)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        
        ssh.connect(self.ssh_address, self.ssh_port, self.ssh_user, self.ssh_password)

        stdin, stdout, stderr = ssh.exec_command(command)

        # Print the command output
        print(stdout.read().decode())

        # Close the SSH connection
        ssh.close()