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
