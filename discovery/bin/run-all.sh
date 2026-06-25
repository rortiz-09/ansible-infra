#!/usr/bin/env bash
# Orquestador del auto-discovery. Pensado para que el servidor de NetBox lo invoque
# por cron a traves de la relacion de confianza con ansible-core, por ejemplo:
#   ssh ansible_root@172.19.31.9 'cd ~/aws-netbox-autodiscovery && bin/run-all.sh'
#
# Cada fuente corre por separado: si una falla, las demas siguen. Los secretos se
# leen del entorno (NETBOX_TOKEN, VCENTER_USER, VCENTER_PASS y credenciales AWS).
set -uo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source .venv/bin/activate

log() { echo "[$(date -u +%FT%TZ)] $*"; }

log "Inicio del auto-discovery"

log "Fuente AWS"
ansible-playbook playbooks/autodiscovery.yml || log "AWS termino con errores"

log "Fuente vCenter"
ansible-playbook playbooks/vcenter-to-netbox.yml || log "vCenter termino con errores"

log "Aplicaciones por servidor"
ansible-playbook playbooks/apps-to-netbox.yml || log "Aplicaciones termino con errores"

log "Fin del auto-discovery"
