from __future__ import annotations
import os
import tempfile
import arcgis
import datetime as _dt
import json
import os
import sys
import time
import arcgis
from arcgis.gis import GIS
from arcgis.gis.admin import PortalAdminManager
import pandas as pd

# import boto3
import concurrent.futures
import datetime as _dt
from typing import Any

print(arcgis.__file__)
print(arcgis.__version__)

import urllib.request


def handle_fiddler():
    proxies = urllib.request.getproxies()
    if proxies == {}:
        proxies = None
    else:
        proxies['https'] = proxies['https'].replace("https", "http")
    return proxies


proxies = handle_fiddler()


def get_logs(gis: GIS, record_type: str = 'portal'):
    admin: PortalAdminManager = gis.admin
    servers: dict[str, list[str, Any]] = {admin.url: []}
    days_back: int
    ref: dict[str, Any] = {admin.url: admin.logs}
    start: _dt.datetime = _dt.datetime.now()
    jobs = {}
    if record_type == "portal":
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as tp:
            # gather the portal logs
            #
            days_back = 1  # admin.logs.settings.get("maxLogFileAge", 90)
            for d in range(days_back):
                future = tp.submit(
                    admin.logs.query,
                    **{
                        "start_time": start - _dt.timedelta(days=d),
                        "end_time": start - _dt.timedelta(days=d + 1),
                    },
                )
                jobs[future] = {
                    "server": admin.url,
                    'start_time': start - _dt.timedelta(days=d),
                    'end_time': start - _dt.timedelta(days=d + 1),
                }
    elif record_type == "server":
        # gather the server logs
        #
        for server in admin.servers.list():
            servers[server.url] = []
            ref[server.url] = server
            days_back = 1  # server.logs.settings.get("maxLogFileAge", 90)
            for d in range(days_back):
                future = tp.submit(
                    server.logs.query,
                    **{
                        "start_time": start - _dt.timedelta(days=d),
                        "end_time": start - _dt.timedelta(days=d + 1),
                    },
                )
                jobs[future] = {
                    "server": server.url,
                    'start_time': start - _dt.timedelta(days=d),
                    'end_time': start - _dt.timedelta(days=d + 1),
                }

    #  Push the log entries into the servers.
    #
    for job in concurrent.futures.as_completed(jobs):
        try:
            records = job.result()
            servers[jobs[job]['server']].extend(
                records.get("logMessages", [])
            )
        except:
            # retry the operation on 504 timeout
            params = jobs[job]
            server_url = params.pop('server')
            print('retrying the query')
            time.sleep(2)
            servers[server_url].extend(ref[server_url].logs.query(**params))
    for key in servers.keys():
        data = servers[key]
        fn: str = f"{urllib.parse.urlparse(key).path[1:].replace('/', '_')}_{(start - _dt.timedelta(days=d)).strftime('%Y%m%dT%H%M%S')}-{(start - _dt.timedelta(days=d + 1)).strftime('%Y%m%dT%H%M%S')}.csv"
        csv_path = os.path.join(tempfile.gettempdir(), fn)
        df = pd.DataFrame(data=data)
        df.to_csv(csv_path)
        servers[key] = csv_path

    return servers


def store_logs(logs: dict, record_type: str, gis: GIS):
    """stores the logs into a single folder on the enterprise."""
    cm = gis.content
    cm.create_folder(record_type)
    for key, value in logs.items():
        item = cm.add(
            item_properties={
                "title": os.path.basename(value).replace(".csv", ""),
                "type": "CSV",
            },
            data=value,
            folder=record_type,
        )
        logs[key] = item
    print(f"uploaded: {len(logs)} log(s)")


if __name__ == "__main__":
    url: str = os.environ['SITE_URL']
    username: str = os.environ['ACCOUNT']
    password: str = os.environ['CREDENTIALS']
    record_type: str = "portal"
    gis: GIS = GIS(
        url=url,
        username=username,
        password=password,
        verify_cert=False,
        proxy=proxies,
    )
    logs: dict[str, Any] = get_logs(gis=gis, record_type=record_type)
    store_logs(logs=logs, record_type=record_type, gis=gis)
    print('See you next time, Space Cowboy!')
