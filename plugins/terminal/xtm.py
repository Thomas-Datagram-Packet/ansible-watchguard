#!/usr/bin/python
# Copyright WatchGuard Technologies, Inc.
# GNU General Public License v3.0+

DOCUMENTATION = """
---
name: xtm

description:
 - Handles Firebox CLI prompts, session lifecycle, and privilege escalation for network_cli

notes:
 - Set ansible_command_timeout in the playbook to avoid default 30-second timeout issues.

authors:
 - Thomas-Datagram-Packet
 - WatchGuard Technologies, Inc. all rights reserved

"""

import re
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.connection import Connection
from ansible.module_utils._text import to_text
from ansible.plugins.terminal import TerminalBase

class TerminalModule(TerminalBase):
        """WatchGuard Firebox terminal handler for network_cli"""

        terminal_stdout_re = [
                re.compile(br"[A-Za-z0-9_-]+(\(config(/[A-Za-z0-9_-]+)*\))?#\s*$")
        ]

        def _get_prompt(self):
                return self._connection.get_prompt()

        def on_open_shell(self):
                """ Called when Ansible opens interactive shell """
                return

        def on_close_shell(self):
                """
                MANDATORY: Send 'exit' to properly terminate Firebox session
                Firebox could requires explicit session termination to allow new connections
                """

                try:
                        while True:
                                prompt = self._get_prompt()
                                if b"/policy)" in prompt:
                                        self._connection.send_command(b"apply\n") #apply configuration (only for policy mode)
                                        self._connection.send_command(b"exit\n")
                                elif b"(config" in prompt:  # still in config mode
                                        self._connection.send_command(b"exit\n")
                                else:  # top-level, session ready to close
                                        self._connection.send_command(b"exit\n")
                                        break
                        return
                except Exception as e:
                                raise AnsibleConnectionFailure("Failed to exit Firebox session: %s" % to_text(e))

        def on_become(self, passwd=None):
                """ Enter configuration mode """
                if not self._connection:
                        raise AnsibleConnectionFailure('No connection available for become()')
                self._connection.send_command(b'configure\n')

        def on_unbecome(self, passwd=None):
                """ Exit configuration mode back to operational """
                if not self._connection:
                        return
                self._connection.send(b'exit\n')

        def normalize_line(self, text):
                """ Clean single line of CLI output and removes carriage returns, trailing whitespace """
                return to_text(text, errors='surrogate_or_strict').rstrip('\r\n ')
