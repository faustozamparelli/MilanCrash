#!/usr/bin/env python3
from pathlib import Path
import sys

import requests

RAW_DIR = Path("./data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

EUDA_WASTEWATER_CSV_URL = (
    "https://www.euda.europa.eu/sites/default/files/data/data-nodes/33337/versions/5/"
    "ww2026-all-data_en.csv"
)
DEST_FILENAME = "euda_wastewater_ww2026_all_cities.csv"
TIMEOUT = 120


def download(url: str, dest: Path) -> None:
    with requests.get(url, stream=True, timeout=TIMEOUT) as response:
        response.raise_for_status()
        with open(dest, "wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    output_file.write(chunk)


def main() -> None:
    destination = RAW_DIR / DEST_FILENAME
    download(EUDA_WASTEWATER_CSV_URL, destination)
    print(f"Downloaded: {destination}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - defensive script entrypoint
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
