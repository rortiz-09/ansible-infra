# Certificados internos AD CS desde Ansible

Este playbook emite certificados TLS internos desde `XTRIM-Root-CA` en `XTRIMAD-CS` y deja un paquete listo para IIS, Nginx, Apache, HAProxy o balanceadores que acepten archivos PEM/PFX.

La automatizacion sigue la bitacora del cambio `*.xtrim.tv` del vault: usa el servidor `192.168.59.125`, no reinicia servicios de aplicaciones y no distribuye certificados a servidores finales. Solo emite y prepara el paquete.

## Archivo principal

```text
playbooks/windows/adcs_issue_certificate_package.yml
```

## Que genera

Para `api-dev.xtrim.com.ec`, el paquete queda en el ADCS bajo:

```text
C:\ProgramData\Ansible\certs\api-dev-xtrim-com-ec\
```

Contenido del ZIP:

```text
api-dev-xtrim-com-ec-2026.crt
api-dev-xtrim-com-ec-2026.fullchain.pem
api-dev-xtrim-com-ec-2026.key
api-dev-xtrim-com-ec-2026.pfx
api-dev-xtrim-com-ec-2026.pfx.pass
xtrim-root-ca.pem
```

La contrasena del PFX se crea automaticamente si no se entrega una por variable.

## Primera prueba sin crear nada

Este es el modo recomendado para validar CA, DNS y parametros. No emite certificado y no crea llaves.

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml
```

Tambien puedes indicar otro nombre sin crear nada:

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_common_name=balanceador.xtrim.com.ec \
  -e cert_dns_names='["balanceador.xtrim.com.ec"]'
```

## Emision real

Ejecutar solo cuando el dry-run salga limpio.

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_dry_run=false
```

Para otro certificado:

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_dry_run=false \
  -e cert_common_name=balanceador.xtrim.com.ec \
  -e cert_dns_names='["balanceador.xtrim.com.ec"]'
```

Para un wildcard:

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_dry_run=false \
  -e cert_common_name='*.xtrim.com.ec' \
  -e cert_dns_names='["*.xtrim.com.ec","xtrim.com.ec"]' \
  -e cert_friendly_name=wildcard-xtrim-com-ec
```

## Vigencia de 20 anios

Por defecto el playbook solicita 20 anios y cambia temporalmente la vigencia de la plantilla `WebServer`, luego la restaura.

Esto requiere una cuenta con permisos sobre Certificate Templates. Si la cuenta no tiene permisos, el playbook se detiene antes de emitir.

Si solo quieres emitir con la vigencia actual de la plantilla:

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_dry_run=false \
  -e cert_manage_template_validity=false
```

La CA raiz tambien limita la fecha final. Si la CA vence antes de los 20 anios pedidos, AD CS puede emitir con una fecha menor.

## Contrasena del PFX

Recomendado: dejar que el playbook cree una contrasena aleatoria y la guarde en el archivo `.pfx.pass` dentro del paquete.

Si necesitas ingresar una contrasena definida:

```bash
ansible-playbook -i inventories/windows_static.ini playbooks/windows/adcs_issue_certificate_package.yml \
  -e cert_dry_run=false \
  -e cert_pfx_password='CAMBIAR_POR_UNA_CLAVE_SEGURA'
```

Evita dejar esa contrasena en historiales de shell. Para uso regular, guardarla en Ansible Vault.

## Validaciones esperadas

Antes de emitir, el playbook valida:

- servicio `CertSvc` en ejecucion;
- respuesta de la CA con `certutil -ping`;
- resolucion DNS de los nombres solicitados, excepto wildcards;
- que el CN este incluido en los SAN.

Despues de emitir, reporta:

- `Subject`;
- `Thumbprint`;
- `NotBefore`;
- `NotAfter`;
- ruta del paquete;
- ruta del ZIP.

## Notas de seguridad

- No copia certificados a servidores de aplicacion.
- No reinicia IIS, Nginx, Apache, HAProxy ni balanceadores.
- No escribe credenciales en el vault de notas.
- La llave privada queda dentro del ZIP y debe tratarse como secreto.
- Para clientes fuera del dominio, la raiz `XTRIM-Root-CA` debe instalarse por un mecanismo aprobado.
