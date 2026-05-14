#!/usr/bin/python
# Copyright WatchGuard Technologies, Inc.
# GNU General Public License v3.0+

#from __future__ import (absolute_import, division, print_function)
#__metaclass__ = type

DOCUMENTATION ="""
---
name: xtm

description:
  - This xtm plugin provides low-level CLI operations for WatchGuard Firebox devices

authors:
 - Thomas-Datagram-Packet
 - WatchGuard Technologies, Inc. all rights reserved
"""

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.cliconf import CliconfBase
import json

class Cliconf(CliconfBase):
        def __init__(self, *args, **kwargs):
                super(Cliconf, self).__init__(*args, **kwargs)

        def set_cli_prompt_context(self):
                """Firebox prompt: WG(config)#, WG(config/policy)#"""
                if self._connection.connected:
                        self._update_cli_prompt_context(config_context=r"\([^)]+\)\#")
                return

        def get(self, command, **kwargs):
                """Execute command at operationnal command mode"""

                try:
                        return  to_text(self.send_command(command), errors="surrogate_or_strict")
                        """stdout and stderr are converted from bytes to text. Thus, surrogate_or_strict has to be used to handle decoding errors (default error handler in all Python versions supproted by Ansible)"""

                except Exception as e:
                        raise AnsibleConnectionFailure("Failed to import command")

        def get_capabilities(self):
                """Device capabilities."""
                result = super(Cliconf, self).get_capabilities()
                return json.dumps(result)
