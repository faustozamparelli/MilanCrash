#!/usr/bin/env python3
from pathlib import Path
import sys
from urllib.parse import urlparse

import requests

RAW_DIR = Path("./data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

CKAN_SHOW = "https://dati.comune.milano.it/api/3/action/package_show"
TIMEOUT = 60

DATASET = {
    "label": "milan_vehicle_fleet",
    "dataset_url": "https://dati.comune.milano.it/dataset/ds721-parco-veicoli-circolanti",
    "package_name": "ds721-parco-veicoli-circolanti",
    "filename_hint": "milan_vehicle_fleet",
}


def get_package(package_name: str):
    response = requests.get(CKAN_SHOW, params={"id": package_name}, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if not payload.get("success"):
        raise RuntimeError(f"CKAN package_show failed for id: {package_name}")

    package = payload.get("result")
    if not package:
        raise RuntimeError(f"No package found for id: {package_name}")

    return package


def choose_csv_resource(package: dict):
    resources = package.get("resources", [])
    if not resources:
        raise RuntimeError(f"No resources found for package: {package.get('name')}")

    for resource in resources:
        resource_format = (resource.get("format") or "").upper()
        if resource_format == "CSV" and resource.get("url"):
            return resource

    raise RuntimeError(f"No CSV resource found for package: {package.get('name')}")


def infer_extension(resource: dict) -> str:
    resource_format = (resource.get("format") or "").lower()
    if resource_format:
        resource_format = resource_format.replace("esri shape", "zip")
        if resource_format == "geojson":
            return ".geojson"
        if resource_format == "json":
            return ".json"
        if resource_format == "csv":
            return ".csv"
        if resource_format in {"shp", "zip"}:
            return ".zip"

    path = urlparse(resource.get("url", "")).path
    suffix = Path(path).suffix
    return suffix or ".dat"


def download(url: str, destination: Path):
    with requests.get(url, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        with open(destination, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    output_file.write(chunk)


def main():
    package = get_package(DATASET["package_name"])
    resource = choose_csv_resource(package)
    extension = infer_extension(resource)
    filename = f"{DATASET['filename_hint']}{extension}"
    destination = RAW_DIR / filename

    download(resource["url"], destination)
    print(f"Downloaded: {destination}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
