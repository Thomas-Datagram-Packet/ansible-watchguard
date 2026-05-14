#!/usr/bin/python
# Copyright WatchGuard Technologies, Inc.
# GNU General Public License v3.0+

DOCUMENTATION = '''
module: firebox_cli

description:
 - Import commands to firebox
 - Supports every command mode (operational, configuration, policy, pppoe, and further...)
notes:
 - Set ansible_command_timeout in the playbook to avoid default 30-second timeout issues.
 - The ansible VM must be connected once manually through SSH before using the module, so the SSH host key is stored in known_hosts.
 - Be careful on sending multiple commands to the same level of configuration (mode)

author:
 - Thomas-Datagram-Packet
 - WatchGuard Technologies, Inc. all rights reserved
'''

EXAMPLES = '''
- name: change_config
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox

  vars:
    ansible_command_timeout: 3

  tasks:

    - name: Edit interface with config module
      watchguard.firebox.firebox_config:
        command: "ip address 10.0.199.1 255.255.255.0 default-gw 10.0.199.3"
        level: "interface FastEthernet 0"
      become: true

    - name: applied
      watchguard.firebox.firebox_cli:
        command: "show interface"

- name: change_config
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox

  vars:
    ansible_command_timeout: 3

  tasks:

    - name: Add an alias with config module
      watchguard.firebox.firebox_config:
        command: "alias final-test description desc host-ip 1.1.1.3"
        level: "policy"
      become: true

    - name: applied
      watchguard.firebox.firebox_cli:
        command: "show alias"

- name: change_config
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox

  vars:
    ansible_command_timeout: 3

  tasks:

    - name: Edit DNS server of the firebox
      watchguard.firebox.firebox_cli:
        command: "ip dns server 8.8.8.8"
      become: true

    - name: applied
      watchguard.firebox.firebox_cli:
        command:
          - "show interface"
          - "show dns"
          - "show vlan"
'''

RETURN = r""" # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
        to_list
)
import json

def run_module():
        module_args = dict(
                command=dict(type='list', element='str', required=True),
                level=dict(type='str', required=False)
        )
        module = AnsibleModule(
                argument_spec=module_args,
                supports_check_mode=True
        )

        command = to_list(module.params['command'])
        connection = Connection(module._socket_path)
        output = []

        if module.params.get('level'):
                connection.send_command(module.params.get('level'))

                if not command:
                        module.fail_json(msg="command cannot be empty")

                for cmd in command:
                        output.append(connection.send_command(cmd))

                module.exit_json(
                        changed=True,
                        stdout_lines=[output for out in output]
                )
        else:

                if not command:
                        module.fail_json(msg="command cannot be empty")

                for cmd in command:
                        output.append(connection.send_command(cmd))

                module.exit_json(
                        changed=True,
                        stdout=output,
                        stdout_lines=[out.splitlines() for out in output]
                )

def main():
        run_module()

if __name__ == '__main__':
    main()
