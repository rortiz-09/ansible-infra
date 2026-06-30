# Playbooks de hardening por version

Estos playbooks son entradas simples para soporte. Cada archivo apunta al grupo del inventario que corresponde al sistema operativo y version.

Ejemplo de validacion sin cambios:

```bash
ansible-playbook -i inventories/linux_hardening_hosts.ini playbooks/linux/hardening_por_version/rhel_9_apply_safe.yml --limit XTR-SRV-ZBXPRO -e apply_hardening=true --check --diff
```

Ejemplo de aplicacion controlada:

```bash
ansible-playbook -i inventories/linux_hardening_hosts.ini playbooks/linux/hardening_por_version/ubuntu_22_04_apply_safe.yml --limit TVC-SRV-ZAPPINGDEV -e apply_hardening=true
```

Siempre usar `--limit` para iniciar por servidores de desarrollo o pruebas antes de produccion.
