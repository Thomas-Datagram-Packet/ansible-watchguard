# Ansible Collection - watchguard.firebox

This collection provides modules to import commands to Watchguard Fireboxes.

## Install

```bash
ansible-galaxy collection install watchguard.firebox
```

## Modules

- firebox_cli
- firebox_alias
- firebox_interface

## Use

### Inventory file

Create a YAML file contaning your fireboxes.

```YAML
all:
  hosts:
    firebox_1:
      ansible_host: 192.168.1.252
      ansible_user: admin
      ansible_password: password
      ansible_connection: network_cli
      ansible_network_os: watchguard.firebox.xtm
      ansible_port: 4118
```
### Playbook examples

According to the fireboxes configuration, an expilicit exit can be required.
Therefore,  `ansible_command_timeout` is recommanded to avoid a 30-second freeze (default time out duration) a the end of the play

```YAML
- name: Edit interface
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox

  vars:
    ansible_command_timeout: 5

  tasks:
    - name: test 1 change IP
      watchguard.firebox.firebox_interfaces:
        interface: 0
        name: "test_external_ip_and_pppoe_OK"
        ip: "145.67.19.19"
        mask: "255.224.0.0"
        default_gw: "145.66.1.1"

    - name: applied
      watchguard.firebox.firebox_cli:
        command: "show interface"
```

```YAML

- name: Edit configuration
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox

  vars:
    ansible_command_timeout: 3

  tasks:

    - name: Edit IP address
      watchguard.firebox.firebox_cli:
        command: "ip address 10.0.199.1 255.255.255.0 default-gw 10.0.199.3"
        level: "interface FastEthernet 0"

    - name: Example config command 3
      watchguard.firebox.firebox_cli:
        command: "show interface"
```

```YAML

- name: Show configuration
  hosts: firebox_1
  gather_facts: false
  collections:
    - watchguard.firebox
  vars:
    ansible_command_timeout: 5

  tasks:
    - name: Import commands
      watchguard.firebox.firebox_cli:
        command:
          - show interface
          - show vlan
```

### Execute a playbook

Run the playbook:

```
$ ansible-playbook -i ./hosts-WG.yml ./edit-interface.yml -vvv

```
