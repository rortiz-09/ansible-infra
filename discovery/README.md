# Auto-discovery hacia NetBox (Xtrim / BSS)

Conjunto de playbooks que mantienen el CMDB de NetBox al dia a partir de tres
fuentes: AWS, vCenter y los propios servidores (aplicaciones). El principio es
siempre el mismo: las fuentes se leen, NetBox se actualiza de forma idempotente y
nada se borra. Cuando un recurso desaparece de su fuente se marca como dado de
baja, con fecha y usuario, para conservar el historico.

## Arquitectura
Los playbooks y las relaciones de confianza viven en ansible-core. El servidor de
NetBox los dispara por cron, a traves de la confianza con ansible-core, y ansible-core
jala la data de cada fuente:

    NetBox (172.19.24.9)  --cron/ssh-->  ansible-core (172.19.31.9)
                                              |  amazon.aws   -> AWS APIs
                                              |  community.vmware -> vCenter
                                              |  ansible facts -> servidores
                                              `-> escribe en NetBox (API)

Ejemplo de cron en el servidor de NetBox:

    0 6 * * * ssh ansible_root@172.19.31.9 'cd ~/aws-netbox-autodiscovery && bin/run-all.sh' >> /var/log/netbox-discovery.log 2>&1

## Playbooks
- `playbooks/autodiscovery.yml`  AWS: subnets, prefixes, instancias persistentes
  (las efimeras tipo Karpenter no se inventarian), IPs y soft-delete de ausentes.
- `playbooks/vcenter-to-netbox.yml`  vCenter: capacidades, direccionamiento, SO y
  campos vcenter_*. Soft-delete con atribucion de quien elimino (helper de eventos).
- `playbooks/apps-to-netbox.yml`  Aplicaciones por servidor via facts (paquetes,
  servicios y puertos en escucha).

## Instalacion
    ./setup.sh        # crea el venv e instala dependencias (boto3, pynetbox, pyvmomi y colecciones)

## Secretos (por entorno, nunca en el repo)
- `NETBOX_TOKEN`  token de NetBox.
- `VCENTER_USER`, `VCENTER_PASS`  lectura en vCenter.
- Credenciales AWS  perfiles SSO `xtrim-*` o variables de entorno (solo lectura).

## Accesos a solicitar para que funcione desde ansible-core
Hoy ansible-core no alcanza algunos destinos; verificado 2026-06-26. Para operar
como esta disenado, pedir a Redes/SOC abrir el egress de ansible-core hacia:

| Destino | Puerto | Estado actual | Para que |
|---------|--------|---------------|----------|
| ec2.us-east-1.amazonaws.com (y demas endpoints AWS) | 443 | bloqueado | leer AWS |
| inventori.xtrim.com.ec (NetBox) | 443 | bloqueado | escribir en NetBox |
| 192.168.21.9 (vCenter) | 443 | por confirmar | leer vCenter |
| servidores on-premise | 22 / WinRM | por confirmar | facts de aplicaciones |

Ademas: relacion de confianza del servidor de NetBox hacia ansible-core para el
cron, y credenciales AWS de solo lectura disponibles en ansible-core.

Mientras esos accesos se habilitan, la actualizacion se ejecuta desde un host que
si tiene alcance (por ahora la estacion del lider de plataformas).

## Politica
- AWS y vCenter en solo lectura. NetBox solo crea o actualiza, nunca borra.
- Data Analytics queda fuera de alcance.
- Conflictos conocidos (por ejemplo 192.168.0.0/16 de AWS contra la WAN on-premise)
  se dejan marcados para validacion manual, no se sobrescriben.
