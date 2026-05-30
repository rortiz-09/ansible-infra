# Trend Micro Deep Security - pausa y restablecimiento

Playbook:

```bash
playbooks/security/trendmicro_deep_security_control.yml
```

## Objetivo

Automatizar el procedimiento de pausa y restablecimiento del agente Trend Micro Deep Security en servidores Linux y Windows.

El procedimiento original indica:

- Pausar proteccion:
  - Linux: `/opt/ds_agent/dsa_control -r -p "PASSWORD"`
  - Windows: ejecutar `dsa_control -r -p "PASSWORD"` desde `C:\Program Files\Trend Micro\Deep Security Agent`
- Restablecer proteccion:
  - Linux/Windows: ejecutar `dsa_control -a dsm://agents.deepsecurity.trendmicro.com:443/ "tenantID:..." "token:..."`

Los valores sensibles deben vivir en Ansible Vault o en el gestor de secretos aprobado. No deben escribirse en texto plano dentro del repositorio.

## Variables requeridas

Para pausar:

```yaml
trendmicro_uninstall_password: "guardar_en_ansible_vault"
```

Para restablecer:

```yaml
trendmicro_tenants:
  core:
    tenant_id: "guardar_en_ansible_vault"
    token: "guardar_en_ansible_vault"
  pro:
    tenant_id: "guardar_en_ansible_vault"
    token: "guardar_en_ansible_vault"
```

## Ejemplos de ejecucion

Pausar en un servidor especifico:

```bash
ansible-playbook playbooks/security/trendmicro_deep_security_control.yml \
  --limit XTR-SRV-EJEMPLO \
  -e trendmicro_action=pause \
  -e trendmicro_allow_change=true \
  --ask-vault-pass
```

Restablecer tenant Core:

```bash
ansible-playbook playbooks/security/trendmicro_deep_security_control.yml \
  --limit XTR-SRV-EJEMPLO \
  -e trendmicro_action=restore \
  -e trendmicro_tenant=core \
  -e trendmicro_allow_change=true \
  --ask-vault-pass
```

Restablecer tenant Pro:

```bash
ansible-playbook playbooks/security/trendmicro_deep_security_control.yml \
  --limit XTR-SRV-EJEMPLO \
  -e trendmicro_action=restore \
  -e trendmicro_tenant=pro \
  -e trendmicro_allow_change=true \
  --ask-vault-pass
```

## Controles de seguridad del playbook

- Exige `--limit`.
- Exige `trendmicro_allow_change=true`.
- Oculta salidas sensibles con `no_log: true`.
- No guarda contrasenas, tenant IDs ni tokens en el repo.
- Valida que exista el binario del agente antes de ejecutar.
- Usa `serial` para limitar concurrencia.

## Posterior a la ejecucion

Despues de restablecer la proteccion, se debe notificar al area de Ciberseguridad para que verifique conexion y estado en la consola de Vision One.
