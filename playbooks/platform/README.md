# Platform automation playbooks

This folder contains control-node and platform-level automation.

## Bootstrap control node

Run from `XTR-SRV-ANSI-CORE`:

```bash
cd /ansible/projects/ansible-infra
ANSIBLE_LOG_PATH=/dev/null ansible-playbook playbooks/platform/bootstrap_control_node.yml
```

The playbook installs Python packages and Ansible collections required for:

- AWS discovery.
- vCenter discovery.
- NetBox integration.
- Zabbix integration.

Secrets must stay outside Git.

Reports use `/ansible/reports` by default. To change the base path, set:

```bash
export ANSIBLE_REPORT_ROOT=/ansible/reports
```
