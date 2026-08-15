"""
Extraction step: downloads the CMS Medicare Physician & Other Practitioners
by Provider dataset and filters it down to one state while streaming,
so we never hold the full national file in memory.
"""

import requests
import pandas as pd
from pathlib import Path

# Real, currently-hosted CMS file (national, ~all Medicare providers).
# Note: CMS renames this file periodically (new release quarter/year in
# the filename) — if this URL 404s in the future, search data.cms.gov
# for "Medicare Physician & Other Practitioners by Provider" for the
# current link.
SOURCE_URL = "https://data.cms.gov/sites/default/files/2025-11/da4b3b2b-1ee2-4e25-b2fe-012b880afd37/MUP_PHY_R25_P05_V20_D14_Prov.csv"

STATE_FILTER = "CA"  # 2-letter state code; change this if you want a different state
OUTPUT_PATH = Path("data/raw/medicare_provider_ca.csv")
CHUNK_SIZE = 100_000  # rows processed per chunk, keeps memory usage low


def download_and_filter(url: str, state: str, output_path: Path) -> None:
    """
    Streams the CMS CSV in chunks, keeps only rows matching `state`,
    and writes the filtered result to output_path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Requesting {url} ...")
    response = requests.get(url, stream=True, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Download failed with status {response.status_code}. "
            "The file URL may have changed — check data.cms.gov."
        )

    print("Connected. Streaming and filtering rows — this may take a few minutes...")

    first_chunk = True
    total_rows_kept = 0
    state_column = None  # we'll detect the real column name from the first chunk

    reader = pd.read_csv(response.raw, chunksize=CHUNK_SIZE, low_memory=False)

    for i, chunk in enumerate(reader):
        if state_column is None:
            # Find the column that holds the 2-letter state code.
            # CMS names it something like 'Rndrng_Prvdr_State_Abrvtn'.
            candidates = [c for c in chunk.columns if "State" in c and "Abrvtn" in c]
            if not candidates:
                print("Columns found in file:", list(chunk.columns))
                raise RuntimeError(
                    "Could not auto-detect the state column. "
                    "Check the printed column list above and update the script."
                )
            state_column = candidates[0]
            print(f"Detected state column: {state_column}")

        filtered = chunk[chunk[state_column] == state]
        total_rows_kept += len(filtered)

        filtered.to_csv(
            output_path,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )
        first_chunk = False
        print(f"  chunk {i + 1}: kept {len(filtered)} rows (running total: {total_rows_kept})")

    if total_rows_kept == 0:
        raise RuntimeError(
            f"No rows matched state='{state}'. Check the state code or the detected column."
        )

    print(f"\nDone. {total_rows_kept} rows saved to {output_path}")


if __name__ == "__main__":
    download_and_filter(SOURCE_URL, STATE_FILTER, OUTPUT_PATH)