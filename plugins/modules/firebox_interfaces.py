#!/usr/bin/python
# Copyright WatchGuard Technologies, Inc.
# GNU General Public License v3.0+

DOCUMENTATION = '''

module: firebox_interface

description:
 - Configure WatchGuard network interfaces.
 - Supports IP addressing, DHCP server, PPPoE, MTU, link speed, and interface type changes.

notes:
 - Set ansible_command_timeout in the playbook to avoid default 30-second timeout issues.
 - Be careful when editing external interfaces. Removing or changing the only external of a device interface will ask you to enter the default gateway. Thus the configuration won't be applied.
 - The ansible VM must be connected once manually through SSH before using the module, so the SSH host key is stored in known_hosts.
 - Make sure you have installed requirements (ansible, ansible-pylibssh, ansible.netcommon) and be in a virtual environnement where those modules have been installed
author:
 - Thomas-Datagram-Packet
 - WatchGuard Technologies, Inc. all rights reserved

'''

EXAMPLES = '''
- name: change_external_interface
  hosts: firebox_1
  gather_facts: false
  collections:
    - thomas_datagram_packet.firebox

  vars:
    ansible_command_timeout: 5

  tasks:
    - name: Test ppoe static
        thomas_datagram_packet.firebox.firebox_interfaces:
                interface: 0
                name: "PPPOE_STATIC"
                edit_type: "external"
                type_external: "pppoe"
                pppoe_user: "a@a.com"
                pppoe_password: "secret"
                pppoe_static_ip: "48.48.48.48"


- name: change_internal_interface
  hosts: firebox_1
  gather_facts: false
  collections:
    - thomas_datagram_packet.firebox

  vars:
    ansible_command_timeout: 5

  tasks:
    - name: test DHCP
        thomas_datagram_packet.firebox.firebox_interfaces:
                interface: 0
                name: "test_external_DHCP_OK"
                edit_type: custom
                dhcp_server: True
                ip: "10.10.100.1"
                mask: "255.0.0.0"
                dhcp_server_start_ip: "10.10.100.100"
                dhcp_server_domain: "a.local"
                dhcp_server_gateway: "10.10.100.2"
                dhcp_server_end_ip: "10.10.100.120"
                dhcp_server_dns:
                        - "3.3.3.3"
                        - "4.4.4.4
                        - "8.8.8.8"
'''

RETURN = r""" # """

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
        to_list
)
import json

def get_interface(connection, interface):
        """Retrieve interface information. """

        output = connection.send_command(f"show interface {interface}")

        iface_info={}

        key_map = {
                'enabled': "enabled",
                'ip node type': "ip_node_type",
                'link status': "link_status",
                'interface number': "interface_number",
                'interface name': "name",
                'interface type': "type"
        }

        for line in output.splitlines():

                if not line or line.startswith("--"):
                        continue

                if ":" not in line:
                        continue

                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key in key_map:
                        iface_info[key_map[key]] = value

        return iface_info

def build_commands(connection, params):
        """Build list of commands according to given parameters"""

        commands = []

        FIELD_MAP = {
                'name': lambda v: f"name {v}",
                'enable': lambda v: f"enable" if params.get('enable') else "no enable",
                'mtu': lambda v: f"mtu {v}",
                'link_speed': lambda v: f"link-speed {v}",
                'secondary_ip': lambda v: f"secondary {params.get('secondary_addr')} {params.get('secondary_mask')}",
        }

        for key, builder in FIELD_MAP.items():
                value = params.get(key)
                if value is not None:
                        commands.append(builder(value))

        """specific case handling to avoid errors in prompt"""
        if params.get('edit_type'):
                if params.get('edit_type') == 'external':
                        if params.get('type_external') == 'pppoe':

                                '''numbers in the domain of the pppoe username are not parsed, the CLI can't retrive password afterward ex: a@a123.com = no password to provide according to CLI'''
                                commands.append(f"type {params.get('edit_type')} pppoe {params.get('pppoe_user')} {params.get('pppoe_password')}")

                                if params.get('pppoe_static_ip'):
                                        commands.append(f"pppoe static-ip {params.get('pppoe_static_ip')}")

                        elif params.get('type_external') == 'dhcp':
                                commands.append(f"type {params.get('edit_type')} dhcp")

                        else:
                                commands.append(f"type {params.get('edit_type')} default-gw {params['default_gw']}")

                else:
                        commands.append(f"type {params.get('edit_type')}")

        if params.get('ip'):
                if get_interface(connection, params.get('interface')).get('type') == 'external' and not params.get('edit_type'):
                        commands.append(f"ip address {params['ip']} {params['mask']} default-gw {params['default_gw']}")

                else:
                        commands.append(f"ip address {params['ip']} {params['mask']}")

        if params.get('dhcp_server_start_ip'):

                dns_list = params.get('dhcp_server_dns')
                dns_str = ' '.join([f"dns-server {dns}" for dns in dns_list])

                if params.get('dhcp_server_domain') and  params.get('dhcp_server_gateway'):
                        commands.append(f"dhcp server start-addr {params.get('dhcp_server_start_ip')} {params.get('dhcp_server_end_ip')} {dns_str} domain {params.get('dhcp_server_domain')}")
                        commands.append(f"dhcp server default-gateway {params.get('dhcp_server_gateway')}")

                elif not params.get('dhcp_server_domain') and params.get('dhcp_server_gateway'):
                        commands.append(f"dhcp server default-gateway {params.get('dhcp_server_gateway')} {dns_str} start-addr {params.get('dhcp_server_start_ip')} {params.get('dhcp_server_end_ip')}")

                elif params.get('dhcp_server_domain') and not params.get('dhcp_server_gateway'):
                        commands.append(f"dhcp server start-addr {params.get('dhcp_server_start_ip')} {params.get('dhcp_server_end_ip')} {dns_str} domain {params.get('dhcp_server_domain')}")

                elif not params.get('dhcp_server_domain') and not params.get('dhcp_server_gateway'):
                        commands.append(f"dhcp server start-addr {params.get('dhcp_server_start_ip')} {params.get('dhcp_server_end_ip')} {dns_str}")

        return commands

def validate_params(connection, module):
        """Validate module parameters"""

        if module.params.get('edit_type') and get_interface(connection, module.params.get('interface')).get('enabled')=="no":
                module.fail_json(msg="interface is currently disabled, you need to enable it to make configuration effective")

        if module.params.get('edit_type') == 'external' and module.params.get('ip') and not module.params.get('default_gw'):
                module.fail_json(msg="default_gw is required when you are changing an external interface's ip")

        if module.params.get('mtu') and not (68 <=  module.params.get('mtu') <= 9000):
                module.fail_json(msg="mtu must be between 68 and 9000")

        if module.params.get('dhcp_server_dns') and len(params['dhcp_server_dns']) > 3:
                module.fail_json(msg="Maximum 3 DNS servers allowed")


def run_module():

        module_args = dict(
                interface=dict(type='int', required=True),
                name=dict(type='str', required=False),
                enable=dict(type='bool', required=False, default=None),
                ip=dict(type='str', required=False),
                mask=dict(type='str', required=False),
                default_gw=dict(type='str', required=False),

                secondary_addr=dict(type='str', required=False),
                secondary_mask=dict(type='str', required=False),

                dhcp_server_start_ip=dict(type='str', required=False),
                dhcp_server_end_ip=dict(type='str', required=False),
                dhcp_server_gateway=dict(type='str', required=False),
                dhcp_server_domain=dict(type='str', required=False),
                dhcp_server_dns=dict(type='list', elements='str', required=False),

                edit_type=dict(
                        type='str',
                        required=False,
                        choices=['custom','external','trusted','optional']
                ),
                type_external=dict(
                        type='str',
                        required=False,
                        choices=['dhcp','pppoe']
                ),

                mtu=dict(type='int', required=False),
                link_speed=dict(
                        type='str',
                        required=False,
                        choices=[
                                '10-full','10-half',
                                '100-full','100-half',
                                '1000-full','1000-half'
                        ]
                ),
                pppoe_user=dict(
                        type='str',
                        required=False,
                        no_log=True
                ),
                pppoe_password=dict(
                        type='str',
                        required=False,
                        no_log=True
                ),
                pppoe_static_ip=dict(type='str', required=False),
        )
        module = AnsibleModule(
                argument_spec=module_args,
                mutually_exclusive = [
                        ('ip', 'pppoe_user'),
                        ('ip', 'pppoe_password'),
                        ('ip', 'pppoe_static_ip'),
                        ('ip', 'type_external'),
                ],
                required_together=[
                        ('ip', 'mask'),
                        ('pppoe_user','pppoe_password'),
                        ('dhcp_server_start_ip','dhcp_server_end_ip', 'dhcp_server_dns'),
                        ('secondary_addr', 'secondary_mask'),
                ],
                supports_check_mode=True
        )

        connection = Connection(module._socket_path)

        connection.send_command("configure")
        connection.send_command(f"interface fastethernet {module.params['interface']}")

        validate_params(connection, module)

        command = build_commands(connection, module.params)

        if not command:
                module.fail_json(msg="request cannot be empty")

        if module.check_mode:
                module.exit_json(
                        changed=True,
                        commands=command,
                )

        output =[]
        for cmd in command:
                output.append(connection.send_command(cmd))

        module.exit_json(
                changed=True,
                stdout_lines=[out.splitlines() for out in output]
        )

def main():
        run_module()

if __name__ == '__main__':
    main()
