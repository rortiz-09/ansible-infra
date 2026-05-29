#!/usr/bin/env python3
"""Bootstrap Linux trust from a temporary Passbolt-derived target file.

Expected input file:
  /root/.ansible_passbolt_linux_bootstrap.json

The JSON must contain a list of targets:
  [
    {
      "name": "server-name",
      "ip": "192.0.2.10",
      "site": "GYE",
      "platform": "Red Hat Enterprise Linux",
      "candidates": [
        {"account": "server-name", "password": "...", "method": "ip_exact"}
      ]
    }
  ]

Do not commit the JSON input file. It contains temporary credentials.
"""

import base64
import concurrent.futures
import csv
import json
import os
import socket
import subprocess
from datetime import datetime

SECRETS = "/root/.ansible_passbolt_linux_bootstrap.json"
LOG_DIR = "/ansible/logs"
PUBKEY_FILE = "/home/ansible_svc/.ssh/ansible_id.pub"
PRIVATE_KEY = "/home/ansible_svc/.ssh/ansible_id"
MAX_WORKERS = int(os.environ.get("BOOTSTRAP_WORKERS", "10"))


def port_open(ip):
    try:
        with socket.create_connection((ip, 22), timeout=4):
            return True
    except OSError:
        return False


def run(cmd, input_text=None, timeout=18):
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def verify(ip):
    cmd = [
        "sudo",
        "-u",
        "ansible_svc",
        "ssh",
        "-i",
        PRIVATE_KEY,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=6",
        "-o",
        "HostKeyAlgorithms=+ssh-rsa",
        "-o",
        "PubkeyAcceptedAlgorithms=+ssh-rsa",
        f"ansible_svc@{ip}",
        "id -un; sudo -n true && echo SUDO_OK || echo SUDO_FAIL",
    ]
    try:
        proc = run(cmd, timeout=18)
    except subprocess.TimeoutExpired:
        return ("timeout", "unknown", "verify_timeout")

    detail = ((proc.stderr or "") + " " + (proc.stdout or "")).replace("\n", " ")[:240]
    if proc.returncode == 0 and "ansible_svc" in proc.stdout:
        return ("ok", "ok" if "SUDO_OK" in proc.stdout else "failed", "")
    return ("failed", "unknown", detail)


def bootstrap_target(target, pubkey_b64, remote_payload, ssh_opts):
    result = {
        "name": target.get("name", ""),
        "ip": target.get("ip", ""),
        "site": target.get("site", ""),
        "platform": target.get("platform", ""),
        "port22": "unknown",
        "attempts": 0,
        "matched_account": "",
        "root_auth": "not_tested",
        "bootstrap": "not_run",
        "trust_login": "not_tested",
        "sudo": "not_tested",
        "detail": "",
    }

    ip = result["ip"]
    if not ip:
        result["detail"] = "missing_ip"
        return result

    if not port_open(ip):
        result["port22"] = "closed_or_filtered"
        result["detail"] = "tcp_22_timeout"
        return result

    result["port22"] = "open"
    for candidate in target.get("candidates", []):
        result["attempts"] += 1
        password = candidate.get("password")
        if not password:
            continue

        cmd = [
            "sshpass",
            "-p",
            password,
            "ssh",
            *ssh_opts,
            f"root@{ip}",
            f"PUBKEY_B64='{pubkey_b64}' bash -s",
        ]

        try:
            proc = run(cmd, input_text=remote_payload, timeout=22)
        except subprocess.TimeoutExpired:
            result["detail"] = "ssh_root_timeout"
            continue

        if proc.returncode == 0 and "BOOTSTRAP_OK" in proc.stdout:
            result["root_auth"] = "ok"
            result["bootstrap"] = "ok"
            result["matched_account"] = candidate.get("account", "")[:80]
            result["trust_login"], result["sudo"], result["detail"] = verify(ip)
            return result

        result["detail"] = ((proc.stderr or "") + " " + (proc.stdout or "")).replace("\n", " ")[:240]

    if result["root_auth"] != "ok":
        result["root_auth"] = "failed"
        result["bootstrap"] = "failed"
    return result


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_csv = os.path.join(LOG_DIR, f"ansible_passbolt_linux_bootstrap_{run_id}.csv")
    log_json = os.path.join(LOG_DIR, f"ansible_passbolt_linux_bootstrap_{run_id}.json")

    with open(SECRETS, encoding="utf-8") as file:
        targets = json.load(file)

    with open(PUBKEY_FILE, encoding="utf-8") as file:
        pubkey_b64 = base64.b64encode(file.read().strip().encode()).decode()

    remote_payload = """
set -eu
user_name='ansible_svc'
pubkey=$(printf '%s' "$PUBKEY_B64" | base64 -d)
if ! id "$user_name" >/dev/null 2>&1; then useradd -m -s /bin/bash "$user_name"; fi
home_dir=$(getent passwd "$user_name" | cut -d: -f6)
install -d -m 700 -o "$user_name" -g "$user_name" "$home_dir/.ssh"
touch "$home_dir/.ssh/authorized_keys"
chown "$user_name:$user_name" "$home_dir/.ssh/authorized_keys"
chmod 600 "$home_dir/.ssh/authorized_keys"
if ! grep -qxF "$pubkey" "$home_dir/.ssh/authorized_keys"; then printf '%s\n' "$pubkey" >> "$home_dir/.ssh/authorized_keys"; fi
if command -v restorecon >/dev/null 2>&1; then restorecon -RF "$home_dir/.ssh" >/dev/null 2>&1 || true; fi
if command -v sudo >/dev/null 2>&1; then
  printf '%s ALL=(ALL) NOPASSWD:ALL\n' "$user_name" > /etc/sudoers.d/90-ansible_svc
  chmod 440 /etc/sudoers.d/90-ansible_svc
  if command -v visudo >/dev/null 2>&1; then visudo -cf /etc/sudoers.d/90-ansible_svc >/dev/null; fi
fi
echo BOOTSTRAP_OK
"""

    ssh_opts = [
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/home/ansible_svc/.ssh/known_hosts.passbolt",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "PreferredAuthentications=password",
        "-o",
        "PubkeyAuthentication=no",
        "-o",
        "HostKeyAlgorithms=+ssh-rsa",
        "-o",
        "PubkeyAcceptedAlgorithms=+ssh-rsa",
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(
            executor.map(
                lambda target: bootstrap_target(target, pubkey_b64, remote_payload, ssh_opts),
                targets,
            )
        )

    fields = [
        "name",
        "ip",
        "site",
        "platform",
        "port22",
        "attempts",
        "matched_account",
        "root_auth",
        "bootstrap",
        "trust_login",
        "sudo",
        "detail",
    ]
    with open(log_csv, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    with open(log_json, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    summary = {}
    for key in ["port22", "root_auth", "bootstrap", "trust_login", "sudo"]:
        summary[key] = {}
        for result in results:
            summary[key][result[key]] = summary[key].get(result[key], 0) + 1

    print(
        json.dumps(
            {
                "targets": len(results),
                "summary": summary,
                "log_csv": log_csv,
                "log_json": log_json,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
