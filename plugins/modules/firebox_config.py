
#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

author:
    - Your Name (@yourGitHubHandle)

POUR LE EXIT BIEN METTRE DANS LA DOC AJOUTER ansible_command_timeout: DANS LE PLAYBOOK SINON ATTENDS 30 SEC

'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
'''

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
	level= module.params.get('level')
	connection = Connection(module._socket_path)
	connection.send_command("configure")
	output = []

	if level:
		connection.send_command(module.params.get('level'))

		if not command:
                       	module.fail_json(msg="command cannot be empty")

		for cmd in command:
			output.append(connection.send_command(cmd))

		module.exit_json(
			changed=True,
			stdout=output,
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
			stdout_lines=[output for out in output]
		)

def main():
	run_module()

if __name__ == '__main__':
    main()
