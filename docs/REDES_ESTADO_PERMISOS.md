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
