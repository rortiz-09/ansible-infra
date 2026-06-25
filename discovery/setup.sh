#!/usr/bin/env bash
# Instala dependencias (venv + colecciones). Requiere acceso a PyPI y Galaxy.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ansible-galaxy collection install -r requirements.yml
echo "[OK] Dependencias instaladas."
echo "Antes de ejecutar:  export NETBOX_TOKEN=...  y credenciales AWS (perfiles SSO o env)."
echo "Dry-run:  source .venv/bin/activate && ansible-playbook playbooks/autodiscovery.yml --check"
