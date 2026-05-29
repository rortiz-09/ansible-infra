# XTRIM Ansible Infrastructure Automation

Proyecto de automatizacion para operar la infraestructura de XTRIM usando Ansible como motor de orquestacion, NetBox como fuente de verdad, Zabbix como capa de monitoreo, vCenter como fuente tecnica de virtualizacion y AWS como inventario cloud.

La idea central es simple: NetBox define que existe y como debe clasificarse; Ansible valida, configura y reporta; Zabbix confirma salud operativa; vCenter y AWS alimentan datos tecnicos sin reemplazar la fuente de verdad.

## Que permite hacer

- Construir inventario dinamico desde NetBox sin guardar secretos en el repositorio.
- Validar puertos requeridos para operar desde el control node Ansible.
- Preparar bootstrap de llaves SSH para Linux con ejecucion controlada por `--limit`.
- Preparar bootstrap de WinRM para Windows, idealmente con HTTPS y certificados internos.
- Validar calidad del inventario: IP primaria, sitio, plataforma, ambiente, criticidad y rol.
- Revisar alcance de Zabbix agent por host.
- Documentar la matriz de puertos necesaria para Redes/Seguridad.
- Servir como base para playbooks futuros de VMware, AWS, certificados, hardening, reportes y mantenimiento.

## Principios operativos

- NetBox es la fuente de verdad.
- No se borran objetos de NetBox por ausencia en vCenter/AWS; se cambia estado y se documenta.
- Ningun playbook masivo debe ejecutarse sin `--limit`.
- Los secretos viven en Ansible Vault, variables de entorno o un secret manager; nunca en Git.
- Todo cambio debe poder validarse antes con `--check` cuando el modulo lo permita.
- Separar playbooks de validacion, reporte, aplicacion y rollback.

## Estructura

```text
ansible.cfg
requirements.yml
inventories/netbox_inventory.py
group_vars/all/
playbooks/connectivity/check_required_ports.yml
playbooks/linux/bootstrap_ssh_keys.yml
playbooks/windows/bootstrap_winrm_https.yml
playbooks/netbox/validate_inventory.yml
playbooks/zabbix/zabbix_agent_check.yml
docs/PUERTOS_ORQUESTACION.md
```

## Variables requeridas

El inventario dinamico usa variables de entorno:

```bash
export NETBOX_URL="https://inventori.xtrim.com.ec"
export NETBOX_TOKEN="<token_en_vault>"
export NETBOX_VERIFY_SSL="false"
```

En PowerShell:

```powershell
$env:NETBOX_URL = "https://inventori.xtrim.com.ec"
$env:NETBOX_TOKEN = "<token_en_vault>"
$env:NETBOX_VERIFY_SSL = "false"
```

## Primeras validaciones

```bash
ansible-inventory --graph
ansible-playbook playbooks/connectivity/check_required_ports.yml
ansible-playbook playbooks/netbox/validate_inventory.yml --limit linux --check
```

## Distribucion de llaves Linux

La distribucion de llaves existe como playbook, pero esta protegida para exigir `--limit`:

```bash
ansible-playbook playbooks/linux/bootstrap_ssh_keys.yml --limit un_servidor --check
ansible-playbook playbooks/linux/bootstrap_ssh_keys.yml --limit un_servidor
```

Cuando se valide un grupo pequeno, se puede escalar por ambiente:

```bash
ansible-playbook playbooks/linux/bootstrap_ssh_keys.yml --limit env_prod
```

Estado actual del bootstrap:

- 99 servidores Linux quedaron con relacion de confianza completa: llave `ansible_svc` + `sudo` validado.
- La ultima validacion `ansible ping` con `become` termino con `PING_RC=0`.
- Windows quedo en fase de validacion: 3 servidores aceptan WinRM con credenciales administrativas; la mayoria rechaza credenciales aunque `5985` esta abierto.
- Los inventarios operativos se generan en el control node bajo `generated/` y no se versionan porque son salida de ejecucion.
- El detalle de logs, bloqueos y pendientes esta en `docs/REDES_ESTADO_PERMISOS.md`.

## Puertos

La matriz inicial esta en:

```text
docs/PUERTOS_ORQUESTACION.md
```

Incluye NetBox, Zabbix, Linux SSH, Windows WinRM, vCenter, FortiAnalyzer, DNS/AD, AD CS, AWS/Galaxy/PyPI y puertos Zabbix agent.

El estado confirmado por Redes y las pruebas pendientes se documentan en:

```text
docs/REDES_ESTADO_PERMISOS.md
```

## Como leer los archivos del proyecto

- `*.yml`: definiciones declarativas de Ansible. Aqui se describe que validar o cambiar.
- `inventories/netbox_inventory.py`: inventario dinamico temporal que consulta NetBox y genera hosts/grupos.
- `ansible.cfg`: configuracion local para que Ansible use este proyecto.
- `docs/`: memoria operativa para explicar decisiones, puertos y procedimientos.

Ansible usa YAML para playbooks y variables. El archivo Python existe porque NetBox es una fuente dinamica; mas adelante puede evolucionar a un inventory plugin, que es el enfoque recomendado por Ansible para versiones modernas.

## Terraform

No es necesario levantar otro servidor solo para Terraform en la primera fase. Ansible puede operar configuracion, validaciones, agentes, certificados y reportes. Terraform conviene incorporarlo cuando se quiera aprovisionar infraestructura nueva de forma declarativa, especialmente en AWS o vSphere. Puede vivir inicialmente en este mismo repositorio bajo una carpeta `terraform/`, con backend remoto y aprobaciones cuando el proceso madure.

## Creditos y licencia

Este proyecto esta licenciado bajo MIT con atribucion requerida. Cualquier uso publico, derivado o documentacion basada en este trabajo debe mantener credito visible a `XTRIM / Ronny Ortiz TI`.
