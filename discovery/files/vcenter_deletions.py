#!/usr/bin/env python3
"""Devuelve, en JSON, las VMs eliminadas en vCenter en los ultimos N dias con el
usuario que las elimino y la fecha. El playbook de reconciliacion lo usa para
atribuir la baja en NetBox sin borrar el objeto (se conserva como historico).

Salida: {"<nombre_vm>": {"user": "...", "time": "ISO8601"}, ...}
Credenciales por entorno: VCENTER_USER, VCENTER_PASS.
"""
import os
import ssl
import json
import argparse
import datetime

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    context = ssl._create_unverified_context()
    si = SmartConnect(
        host=args.host,
        user=os.environ["VCENTER_USER"],
        pwd=os.environ["VCENTER_PASS"],
        sslContext=context,
    )
    try:
        event_manager = si.content.eventManager
        now = datetime.datetime.now(datetime.timezone.utc)

        spec = vim.event.EventFilterSpec()
        by_time = vim.event.EventFilterSpec.ByTime()
        by_time.beginTime = now - datetime.timedelta(days=args.days)
        spec.time = by_time
        spec.eventTypeId = ["VmRemovedEvent"]

        result = {}
        for event in event_manager.QueryEvents(spec):
            name = getattr(getattr(event, "vm", None), "name", None)
            if not name and "'" in event.fullFormattedMessage:
                # Algunos eventos ya no traen la referencia a la VM; se toma del texto.
                name = event.fullFormattedMessage.split("'")[1]
            user = getattr(event, "userName", "") or "desconocido"
            created = event.createdTime.astimezone(datetime.timezone.utc)
            if name:
                result[name] = {"user": user, "time": created.strftime("%Y-%m-%dT%H:%M:%SZ")}

        print(json.dumps(result))
    finally:
        Disconnect(si)


if __name__ == "__main__":
    main()
