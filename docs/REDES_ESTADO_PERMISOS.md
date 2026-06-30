# Estado de permisos de red para Ansible

Fecha: 2026-05-29

Control node:

```text
XTR-SRV-ANSI-CORE
172.19.31.9
```

## Confirmado por Redes

Redes indica que `XTR-SRV-ANSI-CORE` tiene permisos hacia redes de produccion y que `SSH` y `SNMP` estan configurados.

Destinos visibles en la politica compartida:

```text
PRODUCCION_21
PRODUCCION_59
RED_DEV_GYE
RED_TEST_GYE
SRV_172_MONITOREO
SRV_172_PRODUCCION
```

Servicios visibles en la politica compartida:

```text
TCP/8081
TCP/3000
TCP/5985
TCP/5986
TCP/9090
ICMP/PING
```

Servicios indicados por Redes aunque no todos sean visibles en la captura:

```text
TCP/22    SSH
UDP/161   SNMP polling
UDP/162   SNMP traps, si aplica
```

## Lectura operativa

Con esto ya deberiamos poder avanzar con:

- Validacion de reachability por ICMP hacia redes permitidas.
- Bootstrap/control Linux por `SSH TCP/22`, si efectivamente esta permitido.
- Preparacion Windows por WinRM `TCP/5985` y `TCP/5986`.
- Validaciones SNMP contra equipos de red si se permite `UDP/161`.

## Pendiente de validar desde Ansible

Ejecutar desde `XTR-SRV-ANSI-CORE`:

```bash
nc -vz 172.19.24.9 443       # NetBox API
nc -vz 172.19.24.10 443      # Zabbix API
nc -vz 192.168.59.41 443     # FortiAnalyzer API
nc -vz sts.amazonaws.com 443 # AWS STS/API
nc -vz galaxy.ansible.com 443
nc -vz pypi.org 443
```

Para Linux administrados:

```bash
nc -vz <linux_host> 22
```

Para Windows administrados:

```bash
nc -vz <windows_host> 5986
nc -vz <windows_host> 5985
```

Para SNMP:

```bash
snmpwalk -v2c -c <community> <device_ip> sysName.0
```

No guardar communities SNMP en Git. Usar Ansible Vault o secret manager.

## Permisos que aun deben solicitarse si fallan las pruebas

| Origen | Destino | Puerto | Motivo |
|---|---:|---:|---|
| 172.19.31.9 | NetBox 172.19.24.9 | TCP/443 | Inventario dinamico y fuente de verdad |
| 172.19.31.9 | Zabbix 172.19.24.10 | TCP/443 | API de monitoreo |
| 172.19.31.9 | FortiAnalyzer 192.168.59.41 | TCP/443 | Diagnostico de bloqueos y logs |
| 172.19.31.9 | vCenter GYE/UIO | TCP/443 | Inventario VMware |
| 172.19.31.9 | AWS/Galaxy/PyPI | TCP/443 | Cloud automation y dependencias |
| 172.19.31.9 | DNS internos | UDP/TCP 53 | Resolucion |
| 172.19.31.9 | AD/DC | TCP/UDP 88, TCP 389/636, TCP 3268/3269 | Kerberos/LDAP/GC |
| 172.19.31.9 | NTP | UDP/123 | Tiempo correcto para Kerberos/TLS |

## Proxima accion

1. Ejecutar `playbooks/connectivity/check_required_ports.yml` desde Ansible.
2. Agregar targets representativos Linux/Windows por ambiente.
3. Confirmar si `TCP/22`, `UDP/161` y `UDP/162` estan realmente aplicados en firewall.
4. Si NetBox `443` abre, correr inventario dinamico y validar grupos reales.

## Validacion real desde XTR-SRV-ANSI-CORE - 2026-05-29

Se ejecuto el playbook desde el control node en `/ansible/projects/ansible-infra`.

### Servicios centrales

| Destino | Puerto | Resultado desde Ansible |
|---|---:|---|
| NetBox `172.19.24.9` | TCP/443 | Bloqueado / timeout |
| Zabbix `172.19.24.10` | TCP/443 | Bloqueado / timeout |
| FortiAnalyzer `192.168.59.41` | TCP/443 | Bloqueado / timeout |
| AWS STS `sts.amazonaws.com` | TCP/443 | Bloqueado / timeout |
| Galaxy `galaxy.ansible.com` | TCP/443 | OK |
| PyPI `pypi.org` | TCP/443 | OK |
| GitHub `github.com` | TCP/443 | Bloqueado / timeout |

Impacto:

- Sin NetBox `443`, el inventario dinamico real desde el control node no puede funcionar.
- Sin Zabbix `443`, no se puede automatizar validacion/sincronizacion por API.
- Sin FortiAnalyzer `443`, no se pueden consultar logs de bloqueo automaticamente.
- Sin AWS STS/GitHub `443`, cloud automation y `git pull` directo desde el control node quedan limitados.
- Galaxy/PyPI si funcionan, por lo que dependencias Python/Ansible pueden instalarse desde esos endpoints.

### Linux representativos

| Host/IP | Puerto | Resultado |
|---|---:|---|
| `192.168.59.30` | TCP/22 | OK |
| `192.168.21.175` | TCP/22 | OK |
| `192.168.21.117` | TCP/22 | OK |
| `192.168.21.118` | TCP/22 | OK |
| `192.168.35.11` | TCP/22 | Bloqueado / timeout |
| `192.168.9.29` | TCP/22 | Bloqueado / timeout |

Prueba de confianza:

- La llave de `ansible_svc` existe en `XTR-SRV-ANSI-CORE`.
- Los Linux con `TCP/22` abierto rechazan la llave de `ansible_svc`.
- Resultado: hay red parcial, pero no existe aun relacion de confianza SSH.

### Windows representativos

| Host/IP | Puerto | Resultado |
|---|---:|---|
| `192.168.21.17` | TCP/5985 | OK |
| `192.168.21.42` | TCP/5985 | OK |
| `192.168.21.4` | TCP/5985 | OK |
| `192.168.59.131` | TCP/5985 | OK |
| `192.168.59.54` | TCP/5985 | OK |
| mismos hosts | TCP/5986 | Bloqueado / timeout |

Impacto:

- Se puede iniciar con WinRM HTTP `5985` si la politica lo permite.
- Para operacion segura se recomienda habilitar WinRM HTTPS `5986` usando certificados internos emitidos por `XTRIM-Root-CA`.

### Repositorio Ansible en control node

GitHub `443` esta bloqueado desde el control node. Por eso el repositorio no pudo clonarse via `git clone`.
Se subio una copia del repo por SFTP a:

```text
/ansible/projects/ansible-infra
```

Cuando Redes habilite `github.com:443`, cambiar a operacion normal:

```bash
cd /ansible/projects/ansible-infra
git pull
```

### Solicitud concreta para Redes

Abrir desde `XTR-SRV-ANSI-CORE` (`172.19.31.9`):

| Destino | Puerto | Motivo |
|---|---:|---|
| `172.19.24.9` | TCP/443 | NetBox API / inventario dinamico |
| `172.19.24.10` | TCP/443 | Zabbix API |
| `192.168.59.41` | TCP/443 | FortiAnalyzer API/logs |
| `sts.amazonaws.com` y endpoints AWS necesarios | TCP/443 | AWS STS/API |
| `github.com` | TCP/443 | Git pull/push del repo de automatizacion |
| redes Linux faltantes, ejemplo `192.168.35.0/24`, `192.168.9.0/24` | TCP/22 | Administracion Linux por Ansible |
| Windows administrados | TCP/5986 | WinRM HTTPS recomendado |

### Solicitud concreta para relacion de confianza

Para Linux:

- Instalar la llave publica de `/home/ansible_svc/.ssh/ansible_id.pub` en el usuario remoto definido para Ansible.
- Alternativa: entregar usuario/password temporal con sudo para ejecutar `playbooks/linux/bootstrap_ssh_keys.yml`.

Para Windows:

- Definir cuenta de dominio/servicio para Ansible.
- Habilitar WinRM.
- Migrar a `5986` con certificado interno.

## Bootstrap Linux con credencial temporal - 2026-05-29

Se ejecuto bootstrap desde `XTR-SRV-ANSI-CORE` hacia 174 VMs Linux activas detectadas en NetBox.

Accion realizada en hosts donde fue posible autenticarse como `root`:

- Crear/validar usuario `ansible_svc`.
- Instalar llave publica de `/home/ansible_svc/.ssh/ansible_id.pub`.
- Crear sudoers `/etc/sudoers.d/90-ansible_svc` con `NOPASSWD`.
- Validar login por llave como `ansible_svc`.
- Validar `sudo -n true`.
- Ejecutar `ansible ping` con `become`.

Resumen:

| Estado | Cantidad |
|---|---:|
| Hosts candidatos Linux | 174 |
| `TCP/22` cerrado/filtrado | 36 |
| `TCP/22` abierto | 137 |
| Local control node | 1 |
| Password root correcto y bootstrap OK | 25 |
| Password root rechazado | 112 |
| Timeout autenticando root | 1 |
| Relacion de confianza validada con Ansible ping | 25 |

Logs en control node:

```text
/ansible/logs/ansible_trust_bootstrap_20260529-140015.csv
/ansible/logs/ansible_trust_bootstrap_20260529-140015.json
```

Inventario temporal de hosts confiables:

```text
/ansible/projects/ansible-infra/generated/trusted_linux.ini
```

Comando de validacion usado:

```bash
ANSIBLE_HOST_KEY_CHECKING=False ansible \
  -i /ansible/projects/ansible-infra/generated/trusted_linux.ini \
  trusted_linux \
  -m ping \
  -u ansible_svc \
  --private-key /home/ansible_svc/.ssh/ansible_id \
  -b
```

Hosts con confianza validada:

```text
TVC-SRV-DBPANDORA              192.168.59.113
TVC-SRV-DISTRECOMMERCE        192.168.59.127
TVC-SRV-ELASTICSEARCH         192.168.59.25
TVC-SRV-FRONTCERT             192.168.59.26
TVC-SRV-ZAPPINGDEV            192.168.59.147
TVC-SRV-ZAPPINGPRO            192.168.59.148
XTR-SRV-ANSI-CORE             172.19.31.9
XTR-SRV-BANKDEB               192.168.76.90
XTR-SRV-BASTION-K8S           172.19.16.25
XTR-SRV-BROKERPASM            192.168.59.10
XTR-SRV-CPAPP-K8S             172.19.16.29
XTR-SRV-DBINTRAXTR            192.168.76.50
XTR-SRV-ETCDAPP-K8S           172.19.16.28
XTR-SRV-MASTERNODDES          192.168.77.10
XTR-SRV-MASTERNODTES          192.168.76.25
XTR-SRV-N8NDBPRO              192.168.59.15
XTR-SRV-N8NPRO                192.168.59.14
XTR-SRV-REVERSOPROD           192.168.59.35
XTR-SRV-SFTPGO                172.19.24.12
XTR-SRV-STAGINGTES            192.168.76.10
XTR-SRV-WORKERAPP-K8S         172.19.16.27
XTR-SRV-WORKERNODDES          192.168.77.11
XTR-SRV-WORKERNODTES          192.168.76.24
XTR-SRV-ZBXDBPRO              192.168.59.37
XTR-SRV-ZBXPRO                172.19.24.10
```

Pendientes:

- 36 hosts requieren permiso/red `TCP/22` o revision de firewall local.
- 112 hosts tienen `TCP/22` abierto, pero la credencial root temporal no aplica.
- Varios RHEL 5/6 fallan por algoritmos SSH antiguos; requieren excepcion controlada (`HostKeyAlgorithms`/`PubkeyAcceptedAlgorithms`) o actualizacion SSH.
- Para operar con host key checking estricto, limpiar/normalizar `known_hosts`; la validacion inicial se hizo con `ANSIBLE_HOST_KEY_CHECKING=False`.

## Validacion desde estacion Ronny - 2026-05-29

Estas pruebas fueron hechas desde la estacion de administracion, no desde `XTR-SRV-ANSI-CORE`.
Sirven como referencia, pero la validacion definitiva debe ejecutarse desde el control node.

| Destino | Puerto | Resultado |
|---|---:|---|
| Ansible `172.19.31.9` | TCP/22 | Abierto |
| Ansible `172.19.31.9` | TCP/443 | Timeout/no publicado |
| NetBox `172.19.24.9` | TCP/443 | Abierto |
| Zabbix `172.19.24.10` | TCP/443 | Abierto |
| FortiAnalyzer `192.168.59.41` | TCP/443 | Abierto |
| AWS STS `sts.amazonaws.com` | TCP/443 | Abierto |
| Galaxy `galaxy.ansible.com` | TCP/443 | Abierto |
| PyPI `pypi.org` | TCP/443 | Abierto |

SSH hacia `172.19.31.9` responde, pero no existe autenticacion por llave desde la estacion para `root` ni `ansible_svc`.
Para ejecutar validaciones reales desde el control node hace falta una de estas acciones:

- Registrar la llave publica de la estacion en `authorized_keys` de `root` o `ansible_svc`.
- Usar una credencial temporal y luego dejar acceso por llave.
- Ejecutar manualmente el playbook desde una sesion directa al servidor Ansible.

Comando recomendado cuando exista acceso:

```bash
cd /ansible
ansible-playbook playbooks/connectivity/check_required_ports.yml
```

## Bootstrap Linux con Passbolt - 2026-05-29

Se ejecuto una segunda fase usando el export de Passbolt, tomando solo registros cuyo `Login Name` es exactamente `root`.
No se usaron entradas tipo `root*`, aliases o usuarios derivados.

Criterio aplicado:

- Se excluyeron los hosts que ya tenian relacion de confianza validada.
- Se emparejo credencial contra VM solo por IP exacta o nombre exacto normalizado.
- Se evitaron coincidencias difusas para no aplicar credenciales sobre servidores incorrectos.
- El archivo temporal con passwords se subio solo a `/root/.ansible_passbolt_linux_bootstrap.json` y se elimino al terminar la ejecucion.

Resumen de carga:

| Metrica | Cantidad |
|---|---:|
| VMs leidas desde NetBox | 360 |
| Hosts Linux ya confiables excluidos | 25 |
| Entradas Passbolt con login exacto `root` | 301 |
| Targets Linux restantes emparejados | 116 |
| Coincidencias por IP exacta | 138 |
| Coincidencias por nombre exacto | 3 |

Resultado:

| Estado | Cantidad |
|---|---:|
| Targets evaluados | 116 |
| `TCP/22` abierto | 99 |
| `TCP/22` cerrado/filtrado | 17 |
| Autenticacion root OK y llave instalada | 58 |
| Autenticacion root fallida | 41 |
| Relacion de confianza por llave OK | 58 |
| Hosts con llave y sudo OK | 55 |
| Hosts con llave OK pero sudo fallido | 3 |

Inventarios generados en el control node:

```text
/ansible/projects/ansible-infra/generated/trusted_linux.ini
/ansible/projects/ansible-infra/generated/trusted_linux_all.ini
/ansible/projects/ansible-infra/generated/trusted_linux_no_sudo.ini
```

Estado consolidado:

| Inventario | Cantidad | Uso |
|---|---:|---|
| `trusted_linux.ini` | 80 | Linux con llave y sudo OK para operacion Ansible con `become` |
| `trusted_linux_all.ini` | 83 | Linux con llave validada, incluyendo hosts sin sudo |
| `trusted_linux_no_sudo.ini` | 3 | Revision puntual de sudoers |

Hosts con llave instalada pero sin sudo funcional:

```text
tvc-srv-agdi       192.168.21.243
tvc-srv-gruptvc    192.168.21.123
tvc-srv-xtvcable   192.168.21.129
```

Validacion ejecutada:

```bash
ANSIBLE_STDOUT_CALLBACK=default ANSIBLE_HOST_KEY_CHECKING=False ansible \
  -i /ansible/projects/ansible-infra/generated/trusted_linux.ini \
  trusted_linux \
  -m ping \
  -u ansible_svc \
  --private-key /home/ansible_svc/.ssh/ansible_id \
  -b
```

Resultado:

```text
PING_RC=0
```

Logs en el control node:

```text
/ansible/logs/ansible_passbolt_linux_bootstrap_20260529-142037.csv
/ansible/logs/ansible_passbolt_linux_bootstrap_20260529-142037.json
```

Pendientes Linux:

- Revisar 17 hosts con `TCP/22` cerrado/filtrado desde `XTR-SRV-ANSI-CORE`.
- Revisar 41 hosts donde la credencial root de Passbolt no autentica.
- Revisar servidores antiguos que fallan con `error in libcrypto`; probablemente requieren excepcion SSH legacy o actualizacion del servicio SSH.
- Corregir sudoers en los 3 hosts que ya aceptan llave pero no permiten `sudo -n true`.

Pendiente Windows:

- Construir fase Windows con credenciales administrativas de Passbolt.
- Validar primero alcance por `TCP/5985`.
- Migrar a `TCP/5986` cuando los certificados internos de `XTRIM-Root-CA` esten desplegados.

## Validacion Windows con Passbolt - 2026-05-29

Se instalo `pywinrm` en `XTR-SRV-ANSI-CORE` para permitir pruebas WinRM desde Ansible.

La primera fase fue solo de lectura:

- Tomar del export de Passbolt candidatos con login administrativo (`Administrator`, `Administrador` o `admin`).
- Emparejar solo por IP exacta o nombre exacto normalizado.
- Probar `TCP/5985`.
- Ejecutar `hostname` via WinRM cuando la autenticacion fuera aceptada.
- No se aplicaron cambios en Windows.

Resumen:

| Metrica | Cantidad |
|---|---:|
| Entradas Passbolt administrativas | 211 |
| Targets Windows emparejados | 37 |
| `TCP/5985` abierto | 34 |
| `TCP/5985` cerrado/filtrado | 3 |
| Autenticacion WinRM OK | 3 |
| Credenciales rechazadas | 31 |

Hosts Windows con autenticacion WinRM validada:

```text
tvc-srv-backupAS2          192.168.21.34
XTR-SRV-DES-INVICMIGRA     192.168.77.98
xtr-srv-invic-migra        192.168.21.43
```

Log:

```text
/ansible/logs/ansible_passbolt_windows_validate_20260529-142818.json
```

Lectura operativa:

- La red hacia Windows por `5985` funciona para la mayoria de los candidatos probados.
- El bloqueo principal no es red, sino credenciales rechazadas.
- Para relacion de confianza Windows masiva conviene una cuenta de dominio/servicio para Ansible y WinRM HTTPS `5986`.
- No se recomienda crear usuarios locales masivos en Windows hasta acordar el modelo: dominio, grupo local, GPO y certificado.

## Bootstrap Linux con usuarios privilegiados Passbolt - 2026-05-29

Se ejecuto una tercera fase para Linux restantes usando credenciales privilegiadas del export de Passbolt.

Criterio aplicado:

- Se excluyeron los hosts que ya tenian `ansible_svc` + llave + `sudo` validado.
- Se usaron solo credenciales emparejadas por IP exacta o nombre exacto normalizado.
- Se probaron usuarios con patron privilegiado: `root`, `root-*`, `root_*`, `ansible`, `admin`, `sysadmin`, `tiadmin`, `hostadmin`, `clusteradmin`, `appadmin`, `dev-admin`, `desa-admin`, `dea-admin`, `oda-admin`, `sharedadmin`.
- Para usuarios no-root, la llave solo se instala si el usuario puede elevar a root con `sudo`.
- No se guardaron passwords en Git. Los archivos temporales con secretos se eliminaron al terminar.

Resumen de ejecucion:

| Metrica | Cantidad |
|---|---:|
| VMs leidas desde NetBox | 360 |
| Linux ya confiables con sudo excluidos | 80 |
| Entradas privilegiadas de Passbolt evaluables | 544 |
| Targets Linux restantes emparejados | 70 |
| `TCP/22` abierto | 48 |
| `TCP/22` cerrado/filtrado | 22 |
| Autenticacion privilegiada OK | 19 |
| Bootstrap OK | 19 |
| Llave + sudo OK en primera validacion | 16 |
| Llave OK pero sudo bloqueado por `requiretty` | 3 |

Hosts agregados en esta fase:

```text
TVC-SRV-CLUSTER1                   192.168.59.43
TVC-SRV-COLSOC                     192.168.59.119
TVC-SRV-DBALL1                     192.168.59.206
TVC-SRV-DBALL2                     192.168.59.207
TVC-SRV-DBING                      192.168.59.55
TVC-SRV-FRONTEND                   192.168.59.87
TVC-SRV-MALWAREGYE                 192.168.59.20
tvc-srv-malwareuio                 192.168.21.73
TVC-SRV-MOODLE                     192.168.59.3
TVC-SRV-NESSUS                     192.168.59.59
TVC-SRV-TVGUIA                     192.168.59.175
xtr-srv-ansible-controller-control 192.168.21.12
XTR-SRV-GYELDASH01                 192.168.77.24
XTR-SRV-GYELIPAM01                 192.168.77.25
XTR-SRV-PLAYOPSTES                 192.168.76.15
XTR-SRV-ZBPRUEBA                   192.168.77.6
tvc-srv-agdi                       192.168.21.243
tvc-srv-gruptvc                    192.168.21.123
tvc-srv-xtvcable                   192.168.21.129
```

Los tres ultimos tenian `sudo: sorry, you must have a tty to run sudo`.
Se corrigio puntualmente agregando en `/etc/sudoers.d/90-ansible_svc`:

```text
Defaults:ansible_svc !requiretty
ansible_svc ALL=(ALL) NOPASSWD:ALL
```

Validacion consolidada:

| Estado | Cantidad |
|---|---:|
| Linux con relacion de confianza y sudo validado | 99 |
| `ansible ping` con `become` | OK |
| Codigo final | `PING_RC=0` |

Logs:

```text
/ansible/logs/ansible_passbolt_privileged_linux_20260529-144144.csv
/ansible/logs/ansible_passbolt_privileged_linux_20260529-144144.json
/tmp/ansible_ping_sudo_after_requiretty.txt
```

Pendientes para completar universo Linux:

| Bloqueo | Cantidad | Accion requerida |
|---|---:|---|
| `TCP/22` cerrado/filtrado desde Ansible | 36 | Redes/firewall debe permitir SSH desde `172.19.31.9` o validar firewall local |
| Credenciales rechazadas | 43 | Actualizar Passbolt o entregar cuenta privilegiada correcta |
| Sin credencial emparejada util | 1 | Registrar credencial correcta o ajustar inventario |

Estado global Linux:

| Metrica | Cantidad |
|---|---:|
| Linux activos/staged detectados en NetBox | 176 |
| Linux con confianza + sudo | 99 |
| Linux pendientes | 80 |

## Recomendacion para relacion de confianza Windows

Para llevar Windows a todo el universo no conviene depender de contrasenas locales en Passbolt host por host.
El modelo recomendado es:

1. Crear una cuenta de dominio de servicio para Ansible, por ejemplo `svc_ansible_win`.
2. Crear un grupo AD, por ejemplo `GRP_ANSIBLE_WINRM_ADMIN`.
3. Agregar la cuenta de servicio a ese grupo.
4. Por GPO, agregar `GRP_ANSIBLE_WINRM_ADMIN` al grupo local `Administrators` de los servidores Windows administrados.
5. Habilitar WinRM por GPO.
6. En fase inicial se puede validar por `TCP/5985`; para operacion segura usar `TCP/5986`.
7. Emitir certificados internos desde `XTRIM-Root-CA` para WinRM HTTPS.
8. Abrir desde `XTR-SRV-ANSI-CORE` hacia Windows `TCP/5985` temporal/controlado y `TCP/5986` definitivo/recomendado.
9. Crear inventario Windows en Ansible con `ansible_connection=winrm`.
10. Validar con `ansible.windows.win_ping`.

Ya se instalo `pywinrm` en `XTR-SRV-ANSI-CORE`.
La prueba con Passbolt mostro que la red por `5985` funciona para buena parte de los hosts, pero el bloqueo principal es autenticacion.

## Desbloqueo local Windows - XTR-SRV-DES-INVICMIGRA / 192.168.77.98 - 2026-06-30

Ticket relacionado: `#54358 Desbloqueo de usuario desa-admin para server 77.98`.

Validacion realizada desde estacion administrativa hacia `XTR-SRV-ANSI-CORE` por Paramiko y desde el control node hacia `192.168.77.98` por WinRM `5985`.

Hallazgos:

- Host validado: `xtr-srv-des-invicmigra`.
- IP: `192.168.77.98`.
- La cuenta `desa-admin` no existe como cuenta de dominio en `GRUPOTVCABLE.COM`; `Get-ADUser -Identity desa-admin` no encontro objeto en `DC=grupotvcable,DC=com`.
- `desa-admin` existe como cuenta local del servidor.
- La cuenta local estaba activa (`Account active: Yes`).
- Al momento de revisar, `IsAccountLocked` estaba en `false`; aun asi se ejecuto desbloqueo idempotente con ADSI (`IsAccountLocked = false`).
- Ultimo logon registrado: `2026-06-30 08:51:03`.
- Password last set: `2026-02-23 09:40:21`.
- Grupos locales observados: `Administrators`, `Remote Desktop Users`, `docker-users`, `Users`.
- `Get-LocalUser` estaba disponible, pero `Unlock-LocalUser` no estaba disponible en esa sesion remota; por compatibilidad se uso ADSI `WinNT://<host>/desa-admin,user`.
- El servidor esta unido al dominio `grupotvcable.com`, pero el nombre real reportado por Windows es `XTR-SRV-DES-INV`.
- La cuenta AD `svc_ansible` existe y esta habilitada. UPN observado: `svc_ansible@xtrim.com.ec`.
- Para permisos locales, Windows no pudo traducir `GRUPOTVCABLE\svc_ansible`, pero si tradujo `svc_ansible@xtrim.com.ec`.
- Se agrego `svc_ansible@xtrim.com.ec` a `Administrators` y `Remote Management Users` en `192.168.77.98` usando el playbook `playbooks/windows/ensure_ansible_local_admin.yml`.
- Luego `svc_ansible@GRUPOTVCABLE.COM` valido WinRM Kerberos contra `xtr-srv-des-invicmigra.grupotvcable.com` con `win_ping`.

Evidencia de causa:

- La solicitud indicaba bloqueo por intentos incorrectos.
- En la primera validacion puntual la cuenta ya no figuraba bloqueada, por lo que no se pudo probar que siguiera bloqueada en ese instante.
- La prueba posterior del playbook con ventana de 168 horas encontro eventos del Security Log que explican el bloqueo por intentos incorrectos:
  - `2026-06-29 17:41:13`, EventId `4740`, `TargetUserName=desa-admin`.
  - Fallos `4625` con `Status=0xc000006d` y `SubStatus=0xc000006a` antes del bloqueo, equivalente a credenciales incorrectas/password incorrecto.
  - Origenes observados: `GSPANCHANA-TI` (`192.168.4.20`), `DESKTOP-CI7NJF7` (`192.168.14.12`) y `HGUEVARA-TI` (`192.168.14.7`).
  - Despues del bloqueo aparecieron fallos `4625` con `Status=0xc0000234`, equivalente a cuenta bloqueada.

Comando operativo recomendado desde `XTR-SRV-ANSI-CORE`:

```bash
ansible-playbook playbooks/windows/unlock_local_user.yml \
  -e target_hosts=windows_winrm_http \
  --limit xtr_srv_des_invicmigra
```

Prueba realizada desde `XTR-SRV-ANSI-CORE` con el playbook:

```text
Usuario solicitado: DESA-ADMIN
Usuario normalizado: desa-admin
Hostname: XTR-SRV-DES-INV
LockedOutBefore: false
LockedOutAfter: false
LastLogon: 2026-06-30 08:51:03
PasswordLastSet: 2026-02-23 09:40:21
Action: ADSI IsAccountLocked set to false
```

## Permisos locales de svc_ansible en Windows con relacion de confianza - 2026-06-30

Se actualizo `playbooks/windows/ensure_ansible_local_admin.yml` para garantizar que `svc_ansible@xtrim.com.ec` quede en los grupos locales necesarios para operar por WinRM:

- `S-1-5-32-544`: `Administrators` / `Administradores`.
- `S-1-5-32-580`: `Remote Management Users` / `Usuarios de administracion remota`.

El playbook resuelve los grupos por SID, no por nombre, para funcionar en Windows en ingles o espanol. Tambien valida `DomainRole` y no modifica Domain Controllers salvo que se pase explicitamente `windows_ansible_allow_domain_controllers=true`.

Comando ejecutado desde `XTR-SRV-ANSI-CORE`:

```bash
sudo -n /ansible/bin/with-windows-kerberos env \
  ANSIBLE_CONFIG=/ansible/projects/ansible-infra/ansible.cfg \
  ANSIBLE_COLLECTIONS_PATH=/ansible/projects/ansible-infra/collections \
  ANSIBLE_STDOUT_CALLBACK=default \
  ansible-playbook \
  -i /ansible/inventories/windows_static.ini \
  /ansible/projects/ansible-infra/playbooks/windows/ensure_ansible_local_admin.yml \
  -e target_hosts='windows:windows_winrm_http'
```

Hosts Windows con relacion de confianza activa validados:

| Host Ansible | Host Windows | DomainRole | Resultado |
|---|---|---:|---|
| `xtrimad_cs` | `XTRIMAD-CS` | 3 | `svc_ansible@xtrim.com.ec` ya presente en `Administrators` y `Remote Management Users` |
| `xtr_srv_des_invicmigra` | `XTR-SRV-DES-INV` | 3 | `svc_ansible@xtrim.com.ec` ya presente en `Administrators` y `Remote Management Users` |
| `tvc_srv_arcotel` | `TVC-SRV-ARCOTEL` | 1 | `svc_ansible@xtrim.com.ec` ya presente en `Administradores` y `Usuarios de administracion remota` |

Validacion posterior:

```text
ansible win_ping OK en xtrimad_cs, xtr_srv_des_invicmigra y tvc_srv_arcotel.
ensure_ansible_local_admin.yml RC=0 sobre los tres hosts.
```

## Relacion de confianza Ansible Core hacia Domain Controllers - 2026-06-30

Se creo `playbooks/windows/ensure_ad_remoting_access.yml` para administrar el acceso WinRM de `svc_ansible` en servidores AD/DC desde `XTR-SRV-ANSI-CORE`.

Importante: en Domain Controllers no se manejan grupos locales normales como en un member server. Para remoting se valida el grupo Builtin del dominio con SID `S-1-5-32-580` (`Remote Management Users`) y se confirma conectividad WinRM desde el Core.

Comando ejecutado desde `XTR-SRV-ANSI-CORE`:

```bash
sudo -n /ansible/bin/with-windows-kerberos env \
  ANSIBLE_CONFIG=/ansible/projects/ansible-infra/ansible.cfg \
  ANSIBLE_COLLECTIONS_PATH=/ansible/projects/ansible-infra/collections \
  ANSIBLE_STDOUT_CALLBACK=default \
  ansible-playbook \
  -i /ansible/inventories/windows_static.ini \
  /ansible/projects/ansible-infra/playbooks/windows/ensure_ad_remoting_access.yml \
  --limit 'xtrimad_01:tvc_srvaduio1:tvc_srvaduio2:xtrimad_02'
```

Resultado:

| IP | Host Ansible | Host Windows | Resultado |
|---|---|---|---|
| `192.168.59.235` | `xtrimad_01` | `XTRIMAD-01` | `win_ping` OK con `svc_ansible`; `Remote Management Users` ya presente |
| `192.168.59.234` | `xtrimad_02` | `XTRIMAD-02` | `win_ping` OK con `svc_ansible`; `Remote Management Users` ya presente |
| `192.168.21.42` | `tvc_srvaduio1` | `TVC-SRVADUIO1` | `win_ping` OK con `svc_ansible`; `Remote Management Users` ya presente |
| `192.168.21.26` | `tvc_srvaduio2` | `TVC-SRV-ADUIO2` | `win_ping` OK con `svc_ansible`; `Remote Management Users` ya presente |

Membresia de dominio validada:

```text
Principal: svc_ansible
UPN: svc_ansible@xtrim.com.ec
SID: S-1-5-21-869798867-1268677269-1536833037-50103
Builtin group: Remote Management Users
Builtin group SID: S-1-5-32-580
Action: already_present
```

Play recap:

```text
tvc_srvaduio1  ok=3 changed=0 unreachable=0 failed=0
tvc_srvaduio2  ok=3 changed=0 unreachable=0 failed=0
xtrimad_01     ok=4 changed=0 unreachable=0 failed=0
xtrimad_02     ok=3 changed=0 unreachable=0 failed=0
```
