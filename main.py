from __future__ import annotations
import os
import arcgis
import datetime as _dt
from arcgis.gis import GIS, Item
from arcgis.features import Table, FeatureSet, Feature
import pandas as pd
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

if __name__ == "__main__":
    url: str = os.environ['SITE_URL']
    username: str = os.environ['ACCOUNT']
    password: str = os.environ['CREDENTIALS']
    gis: GIS = GIS(
        username=username,
        password=password,
        verify_cert=False,
        proxy=proxies,
    )
    print(gis.users.me)
    print('See you next time, Space Cowboy!')
