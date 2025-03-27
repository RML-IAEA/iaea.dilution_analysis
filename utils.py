import os
import json
from math import sqrt
from typing import Dict


def ensure_file_exists(file_path: str):
    """
    Ensure the file exists, creating an empty JSON object if it doesn't
    """
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)


def load_json(file_path: str) -> Dict:
    """
    Load JSON file, returning an empty dict if file is empty or invalid
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def read_json(file_path: str) -> Dict:
    """
    Read JSON file, maintaining existing implementation
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def calculate_unc(unc1: float, unc2: float) -> float:
    """
    Calculate combined uncertainty
    """
    return sqrt(unc1**2 + unc2**2)
