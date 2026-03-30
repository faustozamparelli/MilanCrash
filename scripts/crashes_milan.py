#!/usr/bin/env python3
from pathlib import Path
import sys
from urllib.parse import urlparse

import requests

RAW_DIR = Path('./data/raw')
RAW_DIR.mkdir(parents=True, exist_ok=True)

CKAN_SHOW = 'https://dati.comune.milano.it/api/3/action/package_show'
TIMEOUT = 60

DATASETS = [
    {
        'label': 'milan_crashes_monthly_city_ring',
        'dataset_url': 'https://dati.comune.milano.it/dataset/ds178-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-cerchia-cittadina',
        'package_name': 'ds178-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-cerchia-cittadina',
        'filename_hint': 'milan_crashes_monthly_city_ring'
    },
    {
        'label': 'milan_crashes_by_nature',
        'dataset_url': 'https://dati.comune.milano.it/dataset/ds176-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-natura-incidente',
        'package_name': 'ds176-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-natura-incidente',
        'filename_hint': 'milan_crashes_by_nature'
    },
    {
        'label': 'milan_crashes_by_vehicles',
        'dataset_url': 'https://dati.comune.milano.it/dataset/ds179-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-veicoli-coinvolti',
        'package_name': 'ds179-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-veicoli-coinvolti',
        'filename_hint': 'milan_crashes_by_vehicles'
    },
    {
        'label': 'milan_crashes_by_zone',
        'dataset_url': 'https://dati.comune.milano.it/dataset/ds177-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-zona',
        'package_name': 'ds177-trafficotrasporti-incidenti-stradali-persone-infortunate-mese-zona',
        'filename_hint': 'milan_crashes_by_zone'
    },
    {
        'label': 'milan_crashes_monthly',
        'dataset_url': 'https://dati.comune.milano.it/dataset/ds175-trafficotrasporti-incidenti-stradali-persone-infortunate-mese',
        'package_name': 'ds175-trafficotrasporti-incidenti-stradali-persone-infortunate-mese',
        'filename_hint': 'milan_crashes_monthly'
    }
]
def get_package(package_name: str):
    r = requests.get(CKAN_SHOW, params={'id': package_name}, timeout=TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    if not payload.get('success'):
        raise RuntimeError(f'CKAN package_show failed for id: {package_name}')
    package = payload.get('result')
    if not package:
        raise RuntimeError(f'No package found for id: {package_name}')
    return package


def choose_csv_resource(package: dict):
    resources = package.get('resources', [])
    if not resources:
        raise RuntimeError(f'No resources found for package: {package.get("name")}')

    for res in resources:
        res_fmt = (res.get('format') or '').upper()
        if res_fmt == 'CSV' and res.get('url'):
            return res

    raise RuntimeError(f'No CSV resource found for package: {package.get("name")}')


def infer_extension(resource: dict) -> str:
    fmt = (resource.get('format') or '').lower()
    if fmt:
        fmt = fmt.replace('esri shape', 'zip')
        if fmt == 'geojson':
            return '.geojson'
        if fmt == 'json':
            return '.json'
        if fmt == 'csv':
            return '.csv'
        if fmt in {'shp', 'zip'}:
            return '.zip'
    path = urlparse(resource.get('url', '')).path
    suffix = Path(path).suffix
    return suffix or '.dat'


def download(url: str, dest: Path):
    with requests.get(url, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)


def main():
    for ds in DATASETS:
        package = get_package(ds['package_name'])
        resource = choose_csv_resource(package)
        ext = infer_extension(resource)
        filename = f"{ds['filename_hint']}{ext}"
        dest = RAW_DIR / filename

        download(resource['url'], dest)
        print(f"Downloaded: {dest}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)