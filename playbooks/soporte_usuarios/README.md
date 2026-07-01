# Playbooks de soporte de usuarios

Playbooks operativos para Mesa/Soporte sobre usuarios de Active Directory.

## Consola principal

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/soporte_usuarios.yml
```

El playbook pregunta:

- Accion: desbloquear usuario o cambiar contrasena.
- Usuario AD.
- Para cambio de contrasena: modo automatico o manual.
- Si el usuario debe cambiar contrasena en el siguiente inicio.
- Si se debe desbloquear la cuenta si esta bloqueada.

Por defecto usa el grupo `ad_domain_controllers`, valida que DCs responden y ejecuta la operacion una sola vez sobre el primer DC disponible. Si un DC esta caido, sigue con otro disponible del inventario.

## Ejecucion no interactiva

Desbloquear:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/soporte_usuarios.yml \
  -e support_action=desbloquear \
  -e support_user=usuario
```

Cambio de contrasena manual:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/soporte_usuarios.yml \
  -e support_action=cambiar_password \
  -e support_user=usuario \
  -e support_password_mode=manual \
  -e support_custom_password='NuevaContrasena' \
  -e support_must_change_password=true \
  -e support_unlock_after_reset=true
```

Para ocultar la contrasena en la salida:

```bash
-e support_show_password=false
```

Cambio de contrasena automatica:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/soporte_usuarios.yml \
  -e support_action=cambiar_password \
  -e support_user=usuario \
  -e support_password_mode=auto \
  -e support_must_change_password=true \
  -e support_unlock_after_reset=true
```

La contrasena automatica usa:

```text
Xtrim<anio>.<usuario>
```

Si no llega a 14 caracteres, se completa con las letras necesarias de `Soporte`.

## Habilitar o deshabilitar usuario AD

Este playbook es independiente de la consola principal. Pide si se desea habilitar o deshabilitar, luego pide el usuario.

Si el usuario no coincide exactamente, busca coincidencias parecidas en AD y permite seleccionar el usuario correcto por numero.

Interactivo:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/deshabilitar_usuario_ad.yml
```

No interactivo:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/deshabilitar_usuario_ad.yml -e support_account_action=deshabilitar -e support_user=usuario
```

Habilitar:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/deshabilitar_usuario_ad.yml -e support_account_action=habilitar -e support_user=usuario
```

Si el usuario ya esta en el estado solicitado, el playbook lo indica y no marca cambios.

## Habilitar o deshabilitar usuarios en lote

El archivo de ejemplo esta en:

```text
/ansible/projects/ansible-infra/playbooks/soporte_usuarios/usuarios_estado_ad.ini
```

Formato:

```ini
[usuarios]
usuario1
usuario2
usuario3
```

Deshabilitar todos los usuarios del archivo:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/deshabilitar_usuario_ad.yml -e support_account_action=deshabilitar -e support_users_file=/ansible/projects/ansible-infra/playbooks/soporte_usuarios/usuarios_estado_ad.ini
```

Habilitar todos los usuarios del archivo:

```bash
sudo -n /ansible/bin/with-windows-kerberos env ANSIBLE_STDOUT_CALLBACK=default ansible-playbook -i /ansible/inventories/windows_static.ini /ansible/projects/ansible-infra/playbooks/soporte_usuarios/deshabilitar_usuario_ad.yml -e support_account_action=habilitar -e support_users_file=/ansible/projects/ansible-infra/playbooks/soporte_usuarios/usuarios_estado_ad.ini
```
