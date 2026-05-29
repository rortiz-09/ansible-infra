# Publicar en GitHub

Este equipo no tiene GitHub CLI (`gh`) instalado, por lo que la publicacion remota requiere crear primero un repositorio en GitHub desde la web.

## Pasos

1. Crear un repo en GitHub, por ejemplo:
   `xtrim-ansible-infra`

2. Desde PowerShell:

```powershell
cd C:\Users\rortiz\Documents\Ansible-XTRIM-Infra
git remote add origin https://github.com/<usuario_o_org>/xtrim-ansible-infra.git
git branch -M main
git push -u origin main
```

3. Si el remoto ya existe:

```powershell
git remote set-url origin https://github.com/<usuario_o_org>/xtrim-ansible-infra.git
git push -u origin main
```

## Reglas

- No subir tokens, passwords, `.env`, `.vault.yml`, `.pfx`, `.pem` ni llaves privadas.
- Revisar `git status` antes de cada push.
- Usar Pull Requests para cambios grandes.
