# Puertos requeridos para orquestacion Ansible / NetBox / Zabbix / Cloud

Origen principal: `XTR-SRV-ANSI-CORE` (`172.19.31.9`).

## Minimo indispensable

| Origen | Destino | Puerto | Uso |
|---|---:|---:|---|
| 172.19.31.9 | NetBox 172.19.24.9 | TCP/443 | Inventario dinamico y fuente de verdad |
| 172.19.31.9 | Zabbix 172.19.24.10 | TCP/443 | API Zabbix |
| 172.19.31.9 | Linux administrados | TCP/22 | SSH Ansible |
| 172.19.31.9 | Windows administrados | TCP/5986 | WinRM HTTPS recomendado |
| 172.19.31.9 | Windows administrados | TCP/5985 | WinRM HTTP temporal/bootstrap |
| 172.19.31.9 | vCenter GYE/UIO | TCP/443 | API vCenter |
| 172.19.31.9 | AWS/Galaxy/PyPI | TCP/443 | Cloud, colecciones y dependencias |

## Recomendado para operacion completa

| Origen | Destino | Puerto | Uso |
|---|---:|---:|---|
| 172.19.31.9 | FortiAnalyzer 192.168.59.41 | TCP/443 | API/logs para diagnostico de bloqueos |
| 172.19.31.9 | DNS internos | UDP/TCP 53 | Resolucion de nombres |
| 172.19.31.9 | AD/DC | TCP/UDP 88 | Kerberos |
| 172.19.31.9 | AD/DC | TCP 389/636 | LDAP/LDAPS |
| 172.19.31.9 | AD/DC | TCP 3268/3269 | Global Catalog |
| 172.19.31.9 | NTP | UDP 123 | Sincronizacion de tiempo |
| 172.19.31.9 | AD CS / CRL | TCP 80/443 | CRL/AIA por HTTP/HTTPS si se publica |
| 172.19.31.9 | AD CS remoto | TCP 135 + 49152-65535 | RPC/DCOM si se emiten certs por RPC remoto |
| Zabbix server/proxy | Hosts administrados | TCP 10050 | Agent passive |
| Hosts administrados | Zabbix server/proxy | TCP 10051 | Agent active/trapper |

## Terraform

No hace falta otro servidor solo para Terraform al inicio. Ansible puede orquestar configuracion y tareas operativas; Terraform conviene para aprovisionamiento declarativo de infraestructura nueva, especialmente AWS/vSphere.

Recomendacion:
- Fase 1: Ansible desde `XTR-SRV-ANSI-CORE` para configuracion, hardening, agentes, certificados, reportes.
- Fase 2: agregar Terraform en el mismo control node o runner CI si se aprovisionaran VMs/cloud de forma repetible.
- Fase 3: separar runner Terraform solo si hay varios equipos, estados remotos, aprobaciones y pipelines formales.
