from math import sqrt, pow
import json
from fastapi import HTTPException


def read_json(filepath):
    try:
        with open(filepath) as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        raise HTTPException(status_code=404,
                            detail="Default data file not found.")


def calculate_unc(value1, value2):
    return sqrt(pow(value1, 2) + pow(value2, 2))
