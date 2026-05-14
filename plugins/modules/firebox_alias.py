#!/usr/bin/python
# Copyright WatchGuard Technologies, Inc.
# GNU General Public License v3.0+

DOCUMENTATION = '''
---

module: firebox_alias

description:
 - Edit aliases of the firebox
notes:
 - Set ansible_command_timeout in the playbook to avoid default 30-second timeout issues.
 - The ansible VM must be connected once manually through SSH before using the module, so the SSH host key is stored in known_hosts.
 - Make sure you have installed requirements (ansible, ansible-pylibssh, ansible.netcommon) and be in a virtual environnement where those modules have been installed
author:
 - Thomas-Datagram-Packet
 - WatchGuard Technologies, Inc. all rights reserved
'''

EXAMPLES = '''
- name: change_alias
  hosts: firebox_1
  gather_facts: false
  collections:
    - thomas_datagram_packet.firebox

  vars:
    ansible_command_timeout: 5

  tasks:
    - name: authorized characters in aliases' name and description
      thomas_datagram_packet.firebox.firebox_alias:
        name: "-, space, comma, 00_, +,[,] ., (, 88), *, :, @, /, ;"
        description: "-, space, comma, 00_, [,] +, ., (, 88), *, :, @, /, ;"
        host_range_start_ip: "1.1.1.1"
        host_range_end_ip: "1.1.1.2"

    - name: applied
      thomas_datagram_packet.firebox.firebox_cli:
        command: "show alias"
'''
RETURN = r""" # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
        to_list
)
import json
import re

def build_commands(connection, params):
        """Build list of commands according to given parameters"""

        commands = []

        if params.get('description'):
                FIELD_MAP = {
                        'host_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" host-ip {params.get('host_ip')}",
                        'host_range_start_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" host-range {params.get('host_range_start_ip')} {params.get('host_range_end_ip')} ",
                        'host6_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" host6-ip {params.get('host6_ip')}",
                        'host6_range_start_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" host6-range  {params.get('host6_range_start_ip')} {params.get('host6_range_end_ip')}",
                        'network_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" network-ip {params.get('network_ip')}",
                        'network6_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" network6-ip {params.get('network6_ip')}",
                        'fqdn': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" fqdn {params.get('fqdn')}",
                        'wildcard_ip': lambda v: f"alias \"{params.get('name')}\" description \"{params.get('description')}\" wildcard {params.get('wildcard_ip')} {params.get('wildcard_mask')}",
                }

        else:
                FIELD_MAP = {
                        'host_ip': lambda v: f"alias \"{params.get('name')}\" host-ip {params.get('host_ip')}",
                        'host_range_start_ip': lambda v: f"alias \"{params.get('name')}\" host-range {params.get('host_range_start_ip')} {params.get('host_range_end_ip')} ",
                        'host6_ip': lambda v: f"alias \"{params.get('name')}\" description host6-ip {params.get('host6_ip')}",
                        'host6_range_start_ip': lambda v: f"alias \"{params.get('name')}\" host6-range  {params.get('host6_range_start_ip')} {params.get('host6_range_end_ip')}",
                        'network_ip': lambda v: f"alias \"{params.get('name')}\" network-ip {params.get('network_ip')}",
                        'network6_ip': lambda v: f"alias \"{params.get('name')}\" network6-ip {params.get('network6_ip')}",
                        'fqdn': lambda v: f"alias \"{params.get('name')}\" fqdn {params.get('fqdn')}",
                        'wildcard_ip': lambda v: f"alias \"{params.get('name')}\" wildcard {params.get('wildcard_ip')} {params.get('wildcard_mask')}",
                }

        for key, builder in FIELD_MAP.items():
                value = params.get(key)
                if value is not None:
                        commands.append(builder(value))

        return commands

def validate_params(connection, module):
        """Validate module parameters"""

        if not re.fullmatch(r'[A-Za-z0-9\s,_.+\-\(\)\[\]:@/;*]*$', module.params.get('name')):
                module.fail_json(msg="forbidden character(s) in name")

        if not re.fullmatch(r'[A-Za-z0-9\s,_.+\-\(\)\[\]:@/;*]*$', module.params.get('description')) :
                module.fail_json(msg="forbidden character(s) in description")

        if module.params.get('network_ip') :
                if "/" not in module.params.get('network_ip') or not 0 < int(module.params.get('network_ip').split("/", 1)[1]) < 32 :
                        module.fail_json(msg="wrong CIDR format, /X required with X between 0 and 32")

        if module.params.get('network6_ip') :
                if "/" not in module.params.get('network6_ip') or not 0 < int(module.params.get('network6_ip').split("/", 1)[1]) < 128 :
                        module.fail_json(msg="wrong CIDR format, /X required with X between 0 and 128")

def run_module():

        module_args = dict(
                name=dict(type='str', required=True),
                description=dict(type='str', required=False),

                host_ip=dict(type='str', required=False),
                host_range_start_ip=dict(type='str', required=False),
                host_range_end_ip=dict(type='str', required=False),

                host6_ip=dict(type='str', required=False),
                host6_range_start_ip=dict(type='str', required=False),
                host6_range_end_ip=dict(type='str', required=False),

                network_ip=dict(type='str', required=False),
                network6_ip=dict(type='str', required=False),
                fqdn=dict(type='str', required=False),

                wildcard_ip=dict(type='str', required=False),
                wildcard_mask=dict(type='str', required=False),

        )
        module = AnsibleModule(
                argument_spec=module_args,
                required_one_of=[
                        ('host_ip','host_range_start_ip','host6_ip','host6_range_start_ip','network_ip','network6_ip','fqdn','wildcard_ip','wildcard_mask'),
                ],
                mutually_exclusive = [
                        ('host_ip','host_range_start_ip','host6_ip','host6_range_start_ip','network_ip','network6_ip','fqdn','wildcard_ip','wildcard_mask'),
                ],
                required_together=[
                        ('host_range_start_ip', 'host_range_end_ip'),
                        ('host6_range_start_ip','host6_range_end_ip'),
                        ('wildcard_ip','wildcard_mask'),
                ],
                supports_check_mode=True
        )

        connection = Connection(module._socket_path)
        validate_params(connection, module)

        connection.send_command("configure")
        connection.send_command("policy")

        command = build_commands(connection, module.params)
        output = []

        if not command:
                module.fail_json(msg="request cannot be empty")

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
