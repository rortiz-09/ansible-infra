#!/usr/bin/env python3
"""Minimal NetBox dynamic inventory for XTRIM.

Environment variables:
  NETBOX_URL   https://inventori.xtrim.com.ec
  NETBOX_TOKEN token stored in Ansible Vault/secret manager
  NETBOX_VERIFY_SSL true/false, default true

This inventory intentionally reads NetBox. It does not write back.
"""

import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request

NETBOX_URL = os.environ.get("NETBOX_URL", "https://inventori.xtrim.com.ec").rstrip("/")
NETBOX_TOKEN = os.environ.get("NETBOX_TOKEN", "")
VERIFY_SSL = os.environ.get("NETBOX_VERIFY_SSL", "true").lower() not in ("0", "false", "no")


def slug(value):
    value = str(value or "unknown").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "unknown"


def nb_get(path):
    if not NETBOX_TOKEN:
        raise SystemExit("NETBOX_TOKEN is required")
    url = f"{NETBOX_URL}/api/{path.lstrip('/')}"
    results = []
    ctx = None if VERIFY_SSL else ssl._create_unverified_context()
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Token {NETBOX_TOKEN}", "Accept": "application/json"})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = json.load(resp)
        if isinstance(data, dict) and "results" in data:
            results.extend(data["results"])
            url = data.get("next")
        else:
            return data
    return results


def ip_addr(obj):
    primary = obj.get("primary_ip4") or obj.get("primary_ip") or {}
    address = primary.get("address") if isinstance(primary, dict) else None
    return address.split("/")[0] if address else None


def label(obj, field):
    val = obj.get(field)
    if isinstance(val, dict):
        return val.get("name") or val.get("slug") or val.get("value") or ""
    return val or ""


def custom(obj, key):
    cf = obj.get("custom_fields") or {}
    return cf.get(key) or cf.get(key.lower()) or ""


def tags(obj):
    return [t.get("slug") or slug(t.get("name")) for t in obj.get("tags") or [] if isinstance(t, dict)]


def add_group(inv, group, host):
    inv.setdefault(group, {"hosts": []})
    if host not in inv[group]["hosts"]:
        inv[group]["hosts"].append(host)


def classify_platform(platform):
    p = platform.lower()
    if any(x in p for x in ["windows", "microsoft"]):
        return "windows"
    if any(x in p for x in ["linux", "red hat", "rhel", "ubuntu", "debian", "centos", "rocky", "oracle"]):
        return "linux"
    return "unknown_os"


def main():
    inv = {"_meta": {"hostvars": {}}}
    objects = []
    for obj in nb_get("virtualization/virtual-machines/?limit=200"):
        obj["_nb_type"] = "vm"
        objects.append(obj)
    for obj in nb_get("dcim/devices/?limit=200"):
        obj["_nb_type"] = "device"
        objects.append(obj)

    for obj in objects:
        host = obj.get("name")
        addr = ip_addr(obj)
        if not host or not addr:
            continue
        platform = label(obj, "platform")
        site = label(obj, "site")
        role = label(obj, "role") or label(obj, "device_role")
        status = label(obj, "status")
        ambiente = custom(obj, "ambiente") or custom(obj, "environment") or "unknown"
        criticidad = custom(obj, "criticidad") or "unknown"
        tag_list = tags(obj)

        inv["_meta"]["hostvars"][host] = {
            "ansible_host": addr,
            "netbox_type": obj.get("_nb_type"),
            "platform": platform,
            "site": site,
            "role": role,
            "status": status,
            "ambiente": ambiente,
            "criticidad": criticidad,
            "netbox_tags": tag_list,
        }

        os_group = classify_platform(platform)
        add_group(inv, "netbox", host)
        add_group(inv, obj.get("_nb_type", "object") + "s", host)
        add_group(inv, os_group, host)
        add_group(inv, "site_" + slug(site), host)
        add_group(inv, "status_" + slug(status), host)
        add_group(inv, "env_" + slug(ambiente), host)
        add_group(inv, "crit_" + slug(criticidad), host)
        for t in tag_list:
            add_group(inv, "tag_" + slug(t), host)

    print(json.dumps(inv, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
