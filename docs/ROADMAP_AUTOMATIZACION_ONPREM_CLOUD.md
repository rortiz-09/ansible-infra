# Roadmap de automatizacion on-premise y cloud

Este documento resume el estado revisado desde `XTR-SRV-ANSI-CORE` y define que falta para operar la infraestructura como una plataforma on-premise con practicas similares a nube.

## Estado validado en Ansible Core

Fecha de revision: 2026-06-30.

Control node:

- Host: `XTR-SRV-ANSI-CORE`.
- Sistema operativo: Red Hat Enterprise Linux 10.2.
- Ansible: `ansible-core 2.16.16`.
- Python: `3.12.13`.
- Proyecto operativo: `/ansible/projects/ansible-infra`.
- Inventario operativo: `/ansible/inventories`.
- Wrapper Kerberos Windows: `/ansible/bin/with-windows-kerberos`.

Capacidades listas:

- Automatizacion Windows por WinRM/Kerberos para AD y servidores con relacion de confianza.
- Consola de soporte para usuarios AD.
- Desbloqueo de usuarios locales Windows.
- Bootstrap y validaciones iniciales de Windows.
- Bootstrap Linux por SSH y sudo.
- Validaciones basicas de Zabbix agent.
- Inventario dinamico planeado desde NetBox.

Estado despues de la habilitacion inicial:

- `aws` CLI instalado para el usuario operativo del Core.
- Librerias Python instaladas: `boto3`, `botocore`, `pynetbox`, `pyVmomi`, `zabbix_utils`.
- Colecciones instaladas en el proyecto: `amazon.aws`, `community.aws`, `community.vmware`, `netbox.netbox`, `community.zabbix`, `community.general`, `community.crypto`, `ansible.netcommon`, `ansible.utils`, `ansible.posix`, `ansible.windows`.
- Directorios de reportes creados en `/ansible/reports`.
- Sintaxis validada para discovery AWS, discovery vCenter, reporte de drift y baseline Windows.
- Baseline Windows probado contra `xtrimad_01` y reporte generado.
- Reporte de drift probado sin discovery previo y reporte generado.

Brechas pendientes:

- No hay credenciales AWS configuradas visibles para el usuario operativo.
- No hay variables vCenter configuradas visibles para discovery: `VCENTER_HOSTNAME`, `VCENTER_USERNAME`, `VCENTER_PASSWORD`.
- El proyecto en `/ansible/projects/ansible-infra` no esta como checkout Git completo; se comporta como copia operativa.
- El `ansible.cfg` del Core usa `stdout_callback = yaml`, pero en algunas ejecuciones se requiere forzar `ANSIBLE_STDOUT_CALLBACK=default`.

## Habilitacion minima del control node

Instalar colecciones del repositorio:

```bash
cd /ansible/projects/ansible-infra
ansible-galaxy collection install -r requirements.yml -p collections
```

Instalar librerias Python necesarias:

```bash
python3 -m pip install boto3 botocore pynetbox pyvmomi zabbix-utils
```

Instalar AWS CLI si el servidor tendra discovery directo de AWS:

```bash
python3 -m pip install awscli
```

Recomendacion de secretos:

- AWS: usar perfiles SSO o variables protegidas por Vault/secret manager.
- NetBox: `NETBOX_URL`, `NETBOX_TOKEN`, `NETBOX_VERIFY_SSL`.
- vCenter: usuario de solo lectura para discovery y usuario separado para cambios.
- Zabbix: token API con permisos minimos.
- Windows: Kerberos con `svc_ansible`, sin guardar password plano en Git.

## Automatizaciones necesarias para operar como nube privada

### Inventario y fuente de verdad

Objetivo: NetBox debe ser la fuente de verdad y Ansible el motor de reconciliacion.

Playbooks recomendados:

- `playbooks/netbox/sync_vcenter_inventory.yml`: sincronizar clusters, hosts, VMs, interfaces e IPs desde vCenter.
- `playbooks/netbox/sync_aws_inventory.yml`: sincronizar cuentas, regiones, VPCs, subnets, EC2, RDS, ELB y tags.
- `playbooks/netbox/validate_required_fields.yml`: validar sitio, ambiente, criticidad, responsable, rol y plataforma.
- `playbooks/netbox/report_inventory_drift.yml`: reportar diferencias entre NetBox, vCenter, AWS y servidores reales.

### Operacion Linux

Objetivo: tener estado, cambios y remediacion controlada por lotes.

Playbooks recomendados:

- `playbooks/linux/baseline_audit.yml`: SO, kernel, uptime, disco, memoria, servicios, Docker, reinicio pendiente.
- `playbooks/linux/security_patch.yml`: parches de seguridad con `--limit`, `serial` y reinicio opcional.
- `playbooks/linux/reboot_controlled.yml`: reinicio por lotes y validacion posterior.
- `playbooks/linux/zabbix_agent_baseline.yml`: instalar y normalizar Zabbix agent.
- `playbooks/linux/docker_host_baseline.yml`: logs, limites, limpieza y parametros daemon.
- `playbooks/linux/certificates_internal_ca.yml`: instalar CA interna en trust store.

### Operacion Windows

Objetivo: convertir WinRM/Kerberos en una base administrable para soporte y plataforma.

Playbooks recomendados:

- `playbooks/windows/baseline_audit.yml`: SO, parches, reinicio pendiente, disco, servicios, roles.
- `playbooks/windows/zabbix_agent_baseline.yml`: agente Zabbix y metadata.
- `playbooks/windows/local_admin_policy_check.yml`: validar grupos locales y cumplimiento.
- `playbooks/windows/winrm_https_baseline.yml`: asegurar WinRM HTTPS con certificado interno.
- `playbooks/windows/certificates_internal_ca.yml`: instalar CA interna.

### Active Directory

Objetivo: reducir tareas manuales y dejar evidencia auditable.

Playbooks recomendados:

- `playbooks/ad/user_support.yml`: evolucionar la consola de soporte actual.
- `playbooks/ad/group_membership_request.yml`: altas y bajas controladas de grupos.
- `playbooks/ad/inactive_users_report.yml`: usuarios inactivos, bloqueados o sin MFA si aplica.
- `playbooks/ad/service_accounts_audit.yml`: cuentas de servicio, expiracion y privilegios.
- `playbooks/ad/dns_records.yml`: administrar registros DNS internos con aprobacion.

### vCenter

Objetivo: discovery, control de capacidad y operaciones repetibles.

Playbooks recomendados:

- `playbooks/vmware/capacity_report.yml`: clusters, datastores, CPU, memoria, snapshots.
- `playbooks/vmware/snapshot_report.yml`: snapshots antiguos y candidatos a limpieza.
- `playbooks/vmware/vm_tag_compliance.yml`: tags obligatorios por ambiente/responsable.
- `playbooks/vmware/vm_power_ops.yml`: encendido/apagado controlado con aprobacion.
- `playbooks/vmware/template_compliance.yml`: plantillas base y versionado.

### AWS

Objetivo: que Ansible pueda descubrir y operar AWS como parte del mismo modelo de plataforma.

Estado actual desde Ansible Core:

- No se pudo consultar AWS porque `aws` CLI no existe en el Core.
- Tampoco estan instalados `boto3` y `botocore`.
- No se observaron perfiles o variables AWS configuradas.

Playbooks recomendados:

- `playbooks/aws/discovery_inventory.yml`: EC2, RDS, ELB, VPC, subnets, security groups, EKS y Lambda.
- `playbooks/aws/tag_compliance.yml`: validar tags obligatorios.
- `playbooks/aws/security_baseline_report.yml`: security groups abiertos, S3 public access, IAM password policy.
- `playbooks/aws/cost_inventory.yml`: reporte por cuenta, region, tag y servicio.
- `playbooks/aws/backup_compliance.yml`: validar backups y retencion.

### Red y seguridad

Objetivo: traer red y seguridad al mismo ciclo de inventario, validacion y drift.

Playbooks recomendados:

- `playbooks/network/device_backup.yml`: backup de configuracion.
- `playbooks/network/ntp_dns_syslog_compliance.yml`: cumplimiento de parametros base.
- `playbooks/network/firewall_rule_report.yml`: reglas expuestas y objetos sin uso.
- `playbooks/security/wazuh_agent_baseline.yml`: cobertura y estado del agente.
- `playbooks/security/trendmicro_agent_baseline.yml`: estado de Deep Security.

## Modelo de operacion recomendado

Separar playbooks en cuatro tipos:

- `discovery`: solo lectura, actualiza reportes o NetBox.
- `audit`: valida estado contra una politica esperada.
- `change`: aplica cambios, exige `--limit`, `serial` y variable de autorizacion.
- `rollback`: revierte cambios cuando sea posible.

Convenciones:

- Ningun cambio masivo sin `--limit`.
- Cambios productivos con `serial`.
- Credenciales fuera de Git.
- Salidas JSON/Markdown guardadas en `/ansible/reports`.
- NetBox como fuente de verdad.
- Zabbix como validacion de salud.
- GitHub como historial de cambios.

## Primeros 10 entregables sugeridos

1. Configurar credenciales AWS seguras en el Core.
2. Configurar credenciales vCenter seguras en el Core.
3. Crear inventario dinamico NetBox estable para Linux y Windows.
4. Ejecutar discovery AWS de solo lectura.
5. Ejecutar discovery vCenter de solo lectura.
6. Crear reporte de snapshots vCenter.
7. Crear validacion de tags obligatorios en AWS y vCenter.
8. Evolucionar reporte de drift NetBox contra vCenter/AWS.
9. Crear pipeline manual para ejecutar playbooks con aprobacion.
10. Definir retencion automatica de `/ansible/reports`.
