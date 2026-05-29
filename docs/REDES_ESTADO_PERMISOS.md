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
