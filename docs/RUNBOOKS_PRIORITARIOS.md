# Runbooks prioritarios XTRIM

Este documento define los primeros runbooks/playbooks que conviene tener para el universo de servidores con relacion de confianza Ansible.

## Criterios de diseno

- NetBox es la fuente de verdad para inventario, sitio, ambiente, plataforma, criticidad y responsables.
- Todo playbook operativo debe poder ejecutarse con `--check` cuando aplique.
- Todo cambio masivo debe exigir `--limit`.
- Los cambios de sistema operativo deben usar `serial` para evitar impactos simultaneos.
- Las tareas con privilegios usan `become: true` y no dependen de usuarios root interactivos.
- Los playbooks viven en Git y no deben contener secretos.
- Los playbooks de cambio deben tener etiquetas (`tags`) para ejecutar fases puntuales.

## Nivel 1 - Base operativa

| Prioridad | Runbook | Objetivo | Estado |
| --- | --- | --- | --- |
| 1 | `playbooks/linux/baseline_audit.yml` | Levantar estado de SO, kernel, disco, memoria, servicios criticos, Docker y necesidad de reinicio. | Creado |
| 2 | `playbooks/linux/security_patch.yml` | Aplicar parches de seguridad de forma controlada, con `--limit`, `serial` y reinicio opcional. | Creado |
| 3 | `playbooks/linux/reboot_controlled.yml` | Reinicio controlado por lotes, esperando que el host vuelva por SSH. | Creado |
| 4 | `playbooks/connectivity/check_required_ports.yml` | Validar puertos de orquestacion desde Ansible. | Existente |
| 5 | `playbooks/linux/bootstrap_ssh_keys.yml` | Instalar relacion de confianza `ansible_svc`. | Existente |

## Nivel 2 - Plataforma y continuidad

| Prioridad | Runbook | Objetivo | Estado recomendado |
| --- | --- | --- | --- |
| 6 | `playbooks/linux/docker_host_baseline.yml` | Normalizar Docker hosts: logs, `fstrim`, daemon defaults, limites systemd. | Pendiente |
| 7 | `playbooks/linux/harness_delegate_health.yml` | Validar delegates Harness, uso de memoria/CPU, estado Docker y rutas criticas. | Pendiente |
| 8 | `playbooks/linux/zabbix_agent_baseline.yml` | Instalar/validar agente Zabbix, tags y metadata desde NetBox. | Pendiente |
| 9 | `playbooks/linux/certificates_internal_ca.yml` | Distribuir CA interna XTRIM y validar trust store. | Pendiente |
| 10 | `playbooks/linux/backup_precheck.yml` | Validar agente/estado de respaldos antes de cambios. | Pendiente |

## Nivel 3 - Descubrimiento para NetBox/Zabbix

| Prioridad | Runbook | Objetivo | Estado recomendado |
| --- | --- | --- | --- |
| 11 | `playbooks/linux/service_discovery.yml` | Descubrir servicios systemd relevantes y preparar carga a NetBox. | Pendiente |
| 12 | `playbooks/linux/disk_inventory.yml` | Inventariar discos, filesystems, LVM, mounts y capacidad. | Pendiente |
| 13 | `playbooks/linux/network_inventory.yml` | Inventariar interfaces, IPs, rutas y DNS para cruzar contra NetBox/IPAM. | Pendiente |
| 14 | `playbooks/linux/database_discovery.yml` | Detectar motores DB y puertos sin modificar servidores. | Pendiente |
| 15 | `playbooks/linux/application_inventory.yml` | Mapear procesos/servicios a aplicaciones de negocio. | Pendiente |

## Nivel 4 - Windows y red

| Prioridad | Runbook | Objetivo | Estado recomendado |
| --- | --- | --- | --- |
| 16 | `playbooks/windows/bootstrap_winrm_https.yml` | Preparar WinRM HTTPS con certificados internos. | Existente |
| 17 | `playbooks/windows/baseline_audit.yml` | Estado Windows: SO, parches, reinicio pendiente, servicios, disco. | Pendiente |
| 18 | `playbooks/network/network_backup.yml` | Backup de configuracion de equipos de red soportados por collections. | Pendiente |
| 19 | `playbooks/network/network_compliance.yml` | Validar SNMP, NTP, syslog, AAA y configuracion minima. | Pendiente |

## Primer flujo operativo recomendado

1. Ejecutar auditoria base:

```bash
ansible-playbook playbooks/linux/baseline_audit.yml --limit trusted_linux
```

2. Revisar salida y hosts con reinicio pendiente.

3. En ventana, aplicar parches de seguridad por ambiente/sitio:

```bash
ansible-playbook playbooks/linux/security_patch.yml --limit linux_prod_gye -e allow_security_patch=true
```

4. Si el playbook informa reinicio requerido, reiniciar por lotes:

```bash
ansible-playbook playbooks/linux/reboot_controlled.yml --limit linux_prod_gye -e allow_reboot=true
```

5. Validar despues del cambio:

```bash
ansible-playbook playbooks/linux/baseline_audit.yml --limit linux_prod_gye
```

## Pendientes de madurez

- Crear grupos dinamicos desde NetBox por `site`, `ambiente`, `criticidad`, `plataforma` y `responsable`.
- Definir naming final de grupos: `linux_prod_gye`, `linux_prod_uio`, `linux_desa`, `linux_test`, `harness`, `zabbix`, `database_candidates`.
- Integrar reportes JSON/Markdown hacia el vault y, luego, hacia NetBox Journal.
- Crear un pipeline de ejecucion con aprobacion manual para playbooks de cambio.
- Agregar pruebas con `ansible-lint` cuando este disponible.

## Referencias

- Ansible playbooks: https://docs.ansible.com/projects/ansible-core/2.16/playbook_guide/index.html
- Privilege escalation `become`: https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html
- Handlers: https://docs.ansible.com/projects/ansible-core/devel/playbook_guide/playbooks_handlers.html
- Best practices: https://docs.ansible.com/ansible/2.9/user_guide/playbooks_best_practices.html
