# Linux hardening operativo

El objetivo es llevar servidores Linux a una postura base de 80 puntos o mas sin aplicar cambios ciegos en produccion.

## Criterio tecnico

La base recomendada es:

- OpenSCAP y SCAP Security Guide para RHEL, Rocky, Oracle Linux y compatibles.
- Ubuntu Security Guide y Lynis para Ubuntu.
- Auditoria generica para Debian y Sangoma cuando no exista un perfil SCAP equivalente.
- Cambios Ansible conservadores para controles comunes: SSH, sysctl, auditd, NTP y firewall opcional.

OWASP no es el marco principal para hardening de sistema operativo. OWASP ayuda mas en aplicaciones web y APIs. Para servidores Linux conviene usar CIS, STIG, OpenSCAP y guias del fabricante.

## Familias detectadas en Ansible Core

Muestra tomada desde `generated/trusted_linux.ini`:

- RHEL 10.1, 10.2.
- RHEL 9.2 a 9.8.
- RHEL 7.2, 7.9.
- Oracle Linux 7.9, 8.10.
- Rocky Linux 8.7.
- CentOS 7.
- Ubuntu 20.04, 22.04, 24.04.
- Debian 12.
- Sangoma 7.

Muestra operativa probada:

| Host | Distro | Familia | Resultado |
| --- | --- | --- | --- |
| `XTR-SRV-SFTPGO` | RHEL 10.1 | `rhel10` | Discovery OK, audit OK, resource audit OK, `--check --diff` OK |
| `XTR-SRV-ZBXPRO` | RHEL 9.7 | `rhel9` | Discovery OK, audit OK |
| `TVC-SRV-NESSUS` | Oracle Linux 8.10 | `oracle8` | Discovery OK, audit OK |
| `TVC-SRV-ZAPPINGDEV` | Ubuntu 22.04 | `ubuntu22` | Discovery OK, audit OK |

## Playbooks

```text
playbooks/linux/hardening_fleet_discovery.yml
playbooks/linux/hardening_audit.yml
playbooks/linux/hardening_tools.yml
playbooks/linux/hardening_openscap_scan.yml
playbooks/linux/hardening_apply_safe.yml
playbooks/linux/resource_provisioning.yml
playbooks/linux/soporte_linux.yml
```

## Flujo recomendado

1. Descubrir distro y familia:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_fleet_discovery.yml --limit XTR-SRV-SFTPGO
```

2. Auditar score interno:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_audit.yml --limit XTR-SRV-SFTPGO
```

3. Instalar herramientas de compliance:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_tools.yml --limit XTR-SRV-SFTPGO -e install_hardening_tools=true
```

4. Ejecutar OpenSCAP si aplica:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_openscap_scan.yml --limit XTR-SRV-SFTPGO
```

5. Aplicar baseline seguro solo con aprobacion:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_apply_safe.yml --limit XTR-SRV-SFTPGO -e apply_hardening=true
```

## Consola para especialistas

```bash
cd /ansible/projects/ansible-infra
ANSIBLE_LOG_PATH=/dev/null ansible-playbook playbooks/linux/soporte_linux.yml
```

Acciones:

- `1`: discovery.
- `2`: auditoria.
- `3`: instalar herramientas.
- `4`: OpenSCAP.
- `5`: aplicar baseline seguro.
- `6`: auditoria de recursos y crecimiento controlado.

## Controles de seguridad

- Todo playbook exige `--limit`.
- Cambios reales requieren variables explicitas como `apply_hardening=true`.
- Desactivar SSH por password no se hace por defecto; requiere `disable_password_ssh=true`.
- Activar firewall no se hace por defecto; requiere `enable_firewall=true`.
- Recursos de filesystem solo crecen con `apply_resource_change=true`.
- Produccion debe ejecutarse con `serial` bajo y despues de pruebas en desarrollo/test.

## Resultado de simulacion segura

Prueba ejecutada contra `XTR-SRV-SFTPGO`:

```bash
ansible-playbook -i generated/trusted_linux.ini playbooks/linux/hardening_apply_safe.yml \
  --limit XTR-SRV-SFTPGO \
  -e apply_hardening=true \
  --check --diff
```

Cambios que aplicaria:

- Crear `/var/backups/xtrim-hardening`.
- Ajustar `PermitRootLogin no`.
- Crear `/etc/sysctl.d/90-xtrim-hardening.conf`.
- Reiniciar `sshd` si hay cambios reales.

Cambios que no aplica por defecto:

- No desactiva `PasswordAuthentication`.
- No habilita firewall.
- No reinicia el servidor.

## Reportes

Los reportes se guardan bajo:

```text
/ansible/reports/linux-hardening
/ansible/reports/linux-resources
```
