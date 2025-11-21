"""
data_prep.py

Utilities to clean and prepare `data_koordinat.csv` for the GA pipeline.

Functions:
- prepare_dataset(input_csv, output_csv=None): reads semicolon CSV with comma decimals,
  converts numeric fields to standard CSV with dot decimals and returns path to cleaned file
  and node dictionary.
"""
import csv
import os
from typing import Tuple, Dict


def _normalize_number(s: str) -> str:
    # replace comma decimal with dot and strip spaces
    return s.replace('\u00A0', '').replace(' ', '').replace(',', '.')


def prepare_dataset(input_csv: str, output_csv: str = None) -> Tuple[str, Dict[int, dict]]:
    """Read `input_csv` (semicolon-separated, comma decimal), write cleaned CSV and return nodes.

    Returns: (cleaned_csv_path, nodes_data)
    nodes_data: dict {index: {'x': float, 'y': float, 'demand': int}}
    """
    if output_csv is None:
        base, ext = os.path.splitext(input_csv)
        output_csv = base + '_cleaned.csv'

    nodes = {}
    with open(input_csv, 'r', encoding='utf-8') as inf:
        # The source file uses semicolon separators
        reader = csv.DictReader(inf, delimiter=';')
        # Normalize fieldnames to common lowercase keys
        for row in reader:
            try:
                idx = int(row.get('index') or row.get('Index') or row.get('idx'))
            except Exception:
                continue
            raw_x = row.get('x') or row.get('X') or ''
            raw_y = row.get('y') or row.get('Y') or ''
            raw_d = row.get('Demand') or row.get('demand') or row.get('D') or '0'
            try:
                x = float(_normalize_number(raw_x))
                y = float(_normalize_number(raw_y))
            except Exception:
                # skip malformed rows
                continue
            try:
                demand = int(_normalize_number(raw_d))
            except Exception:
                demand = 0
            nodes[idx] = {'x': x, 'y': y, 'demand': demand}

    # write cleaned CSV with standard comma delimiter and dot decimals
    with open(output_csv, 'w', encoding='utf-8', newline='') as outf:
        writer = csv.writer(outf)
        writer.writerow(['index', 'x', 'y', 'demand'])
        for idx in sorted(nodes.keys()):
            n = nodes[idx]
            writer.writerow([idx, f"{n['x']:.6f}", f"{n['y']:.6f}", n['demand']])

    return output_csv, nodes


if __name__ == '__main__':
    import sys
    inp = sys.argv[1] if len(sys.argv) > 1 else 'data_koordinat.csv'
    out, nodes = prepare_dataset(inp)
    print(f"Wrote cleaned CSV: {out} (nodes: {len(nodes)})")
