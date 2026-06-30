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
| 17 | `playbooks/windows/unlock_local_user.yml` | Desbloquear cuenta local Windows solicitando el usuario en runtime y registrar evidencia de intentos fallidos/bloqueo. | Creado |
| 18 | `playbooks/windows/ensure_ansible_local_admin.yml` | Agregar `svc_ansible` o un grupo de dominio a administradores locales para operacion WinRM. | Creado |
| 19 | `playbooks/soporte_usuarios/soporte_usuarios.yml` | Consola interactiva para desbloqueo AD y cambio de contrasena de usuarios. | Creado |
| 20 | `playbooks/windows/baseline_audit.yml` | Estado Windows: SO, parches, reinicio pendiente, servicios, disco. | Pendiente |
| 21 | `playbooks/network/network_backup.yml` | Backup de configuracion de equipos de red soportados por collections. | Pendiente |
| 22 | `playbooks/network/network_compliance.yml` | Validar SNMP, NTP, syslog, AAA y configuracion minima. | Pendiente |

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

## Flujo Windows - desbloqueo de usuario local

El playbook solicita siempre el usuario a desbloquear, lo normaliza a minusculas y no acepta dominio en el valor ingresado.

```bash
ansible-playbook playbooks/windows/unlock_local_user.yml \
  -e target_hosts=windows_winrm_http \
  --limit xtr_srv_des_invicmigra
```

Para pasar el target por variable:

```bash
ansible-playbook playbooks/windows/unlock_local_user.yml -e target_hosts=windows_winrm_http --limit xtr_srv_des_invicmigra
```

La salida incluye:

- Estado antes/despues de `IsAccountLocked`.
- `LastLogon`, `PasswordLastSet` y grupos locales del usuario.
- Hasta 20 eventos recientes `4625` y `4740` del Security Log para explicar origen de intentos fallidos o bloqueo.

El permiso permanente de `svc_ansible` debe quedar preferiblemente por GPO agregando un grupo de dominio a `Administrators` y `Remote Management Users`. Para bootstrap puntual por Ansible existe:

```bash
ansible-playbook playbooks/windows/ensure_ansible_local_admin.yml --limit servidor_windows \
  -e windows_ansible_admin_principal='svc_ansible@xtrim.com.ec'
```

Nota: en pruebas contra `192.168.77.98`, Windows no pudo traducir `GRUPOTVCABLE\svc_ansible`, pero si tradujo correctamente el UPN `svc_ansible@xtrim.com.ec`.
El playbook resuelve los grupos locales por SID para soportar Windows en ingles o espanol y bloquea cambios en Domain Controllers salvo autorizacion explicita.

Para Domain Controllers se usa un playbook separado, porque el grupo Builtin del dominio no se administra como grupo local de member server:

```bash
ansible-playbook playbooks/windows/ensure_ad_remoting_access.yml --limit ad_domain_controllers
```

Ese playbook garantiza/verifica `svc_ansible` en `Remote Management Users` por SID `S-1-5-32-580` y luego valida `win_ping` en cada DC.

## Flujo soporte usuarios AD

La consola principal para Mesa/Soporte esta en:

```bash
ansible-playbook playbooks/soporte_usuarios/soporte_usuarios.yml
```

Opciones:

- `1` / `desbloquear`: pide usuario AD, revisa `LockedOut`, desbloquea solo si esta bloqueado e informa si no estaba bloqueado.
- `2` / `cambiar_password`: pide usuario, modo de contrasena, si debe cambiar al siguiente inicio y si debe desbloquear si esta bloqueado.

Contrasena automatica:

```text
Xtrim<anio>.<usuario>
```

Si no completa 14 caracteres, se agregan las letras necesarias de `Soporte`.

Prueba real ejecutada desde `XTR-SRV-ANSI-CORE` contra `acolorado`:

```text
Password manual: valor temporal definido para prueba, no documentado en Git
MustChangeAtNextLogon: true
Bloqueo real generado con 5 intentos fallidos segun politica AD
Desbloqueo con playbook: OK
Segunda corrida de desbloqueo: informa que el usuario no se encuentra bloqueado
Estado final: Enabled=true, LockedOut=false, badPwdCount=0, pwdLastSet=0
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
