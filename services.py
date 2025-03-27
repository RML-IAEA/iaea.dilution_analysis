from math import sqrt
import json
from typing import Dict, List
from fastapi import HTTPException

from models import DilutionData
from utils import calculate_unc
from utils import ensure_file_exists
from utils import load_json
from utils import read_json


# Configuration constants
DEFAULT_FILE_PATH = "data/dilution_data.json"
CUSTOM_FILE_PATH = "data/custom_dilution_data.json"
TRACER_JSON_PATH = "data/tracer_info.json"


class DilutionService:
    """
    Service class to encapsulate dilution-related business logic
    """
    @classmethod
    def get_data_source(cls) -> str:
        """
        Determine the current data source based on file contents
        """
        # Check if custom data file exists and has content
        ensure_file_exists(CUSTOM_FILE_PATH)
        custom_data = load_json(CUSTOM_FILE_PATH)
        return 'custom' if custom_data else 'default'

    def get_data_by(self, dilution_number: int) -> Dict:
        """
        Retrieve dilution data based on the current data source
        """
        file_path = (CUSTOM_FILE_PATH if self.get_data_source() == 'custom'
                     else DEFAULT_FILE_PATH)

        try:
            data = read_json(file_path)
            dilution_data = data.get(str(dilution_number))
            if dilution_data is None:
                raise HTTPException(status_code=404,
                                    detail="Dilution data not found")
            return dilution_data
        except Exception:
            raise HTTPException(status_code=404,
                                detail="Data not found")

    def submit_dilution_data(self, dilution_number: int, data: DilutionData):
        """
        Submit dilution data to the custom data file
        """
        ensure_file_exists(CUSTOM_FILE_PATH)

        # Read existing data
        custom_data = load_json(CUSTOM_FILE_PATH)

        # Add or update the new dilution data
        custom_data[str(dilution_number)] = {
            "m0": {"value": data.m0.value, "uncertainty": data.m0.uncertainty},
            "m1": {"value": data.m1.value, "uncertainty": data.m1.uncertainty},
            "m2": {"value": data.m2.value, "uncertainty": data.m2.uncertainty}
        }
        # Write back to file
        with open(CUSTOM_FILE_PATH, 'w') as f:
            json.dump(custom_data, f, indent=2)

    def get_dilutions(self) -> Dict:
        """
        Retrieve all dilution data based on the current data source
        """
        file_path = (CUSTOM_FILE_PATH if self.get_data_source() == 'custom'
                     else DEFAULT_FILE_PATH)
        return read_json(file_path)

    @staticmethod
    def reset_custom_data():
        """
        Reset the custom data file to an empty state
        """
        with open(CUSTOM_FILE_PATH, 'w') as f:
            json.dump({}, f)

    @staticmethod
    def get_tracers():
        """
        Return a list of all tracers available in the tracer_info.json
        """
        data = read_json(TRACER_JSON_PATH)
        tracers = [tracer["title"] for tracer in data]
        return tracers

    @staticmethod
    def get_tracer(title: str):
        """
        Given a tracer title, return its activity and uncertainty
        """
        data = load_json(TRACER_JSON_PATH)
        for tracer in data:
            if tracer["title"].lower() == title.lower():
                return {
                    "source_id": tracer["source_id"],
                    "activity": tracer["activity"],
                    "uncertainty": tracer["uncertainty"]
                }
        raise HTTPException(status_code=404, detail="Tracer not found")

    @staticmethod
    def get_tracer_by_source_id(source_id: str):
        """
        Given a tracer title, return its activity and uncertainty
        """
        data = load_json(TRACER_JSON_PATH)
        for tracer in data:
            if tracer["source_id"] == source_id:
                return {
                    "title": tracer["title"],
                    "activity": tracer["activity"],
                    "uncertainty": tracer["uncertainty"]
                }
        raise HTTPException(status_code=404, detail="Tracer not found")

    def calculate_net_spike(self, dilution_number: int) -> Dict:
        """
        Calculate net spike for a given dilution number
        """
        data = self.get_data_by(dilution_number)
        net_mass = data["m1"]["value"] - data["m0"]["value"]
        m1_unc = data["m1"]["uncertainty"]
        m0_unc = data["m0"]["uncertainty"]
        net_mass_unc = calculate_unc(m1_unc, m0_unc)
        return {"value": net_mass, "uncertainty": net_mass_unc}

    def calculate_net_dilutant(self, dilution_number: int) -> Dict:
        """
        Calculate net dilutant for a given dilution number
        """
        data = self.get_data_by(dilution_number)
        md_value = data["m2"]["value"] - data["m0"]["value"]
        m2_unc = data["m2"]["uncertainty"]
        m0_unc = data["m0"]["uncertainty"]
        md_unc = calculate_unc(m2_unc, m0_unc)
        return {"value": md_value, "uncertainty": md_unc}

    def calculate_fdil(self, dilution_number: int) -> Dict:
        """
        Calculate dilution factor for a given dilution number
        """
        data = self.get_data_by(dilution_number)
        net_spike = self.calculate_net_spike(dilution_number)
        net_dilutant = self.calculate_net_dilutant(dilution_number)

        m0 = data["m0"]["value"]
        m0_unc = data["m0"]["uncertainty"]
        m1 = data["m1"]["value"]
        m1_unc = data["m1"]["uncertainty"]
        m2 = data["m2"]["value"]
        m2_unc = data["m2"]["uncertainty"]

        fdil = net_spike["value"] / net_dilutant["value"]
        dfdil_dm0 = (m1 - m2) / (m2 - m0)**2
        dfdil_dm1 = 1 / (m2 - m0)
        dfdil_dm2 = -1 * (m1 - m0) / (m2 - m0) ** 2
        fdil_unc = sqrt((dfdil_dm0 * m0_unc) ** 2 +
                        (dfdil_dm1 * m1_unc) ** 2 +
                        (dfdil_dm2 * m2_unc) ** 2)
        return {"value": fdil, "uncertainty": fdil_unc}

    def calculate_tracer_dilution(self, tracer: str) -> List[Dict]:
        """
        Calculate tracer dilution across multiple dilution steps
        """
        data = self.get_dilutions()
        tracer_data = self.get_tracer(tracer)
        # Start with the initial tracer activity and uncertainty
        dilution_activity = tracer_data["activity"]
        tracer_rel_unc = tracer_data["uncertainty"] / tracer_data["activity"]
        total_uncertainty = tracer_data["uncertainty"]

        dilution_results = []

        # Process the first dilution step
        fdil = self.calculate_fdil(1)
        dilution_activity *= fdil['value']
        fdil_rel_unc = fdil['uncertainty'] / fdil['value']

        # For the first dilution, calculate the combined uncertainty
        dilution_unc = calculate_unc(tracer_rel_unc, fdil_rel_unc)
        total_uncertainty = dilution_activity * dilution_unc
        dilution_results.append({
            "dilution_step": 1,
            "value": dilution_activity,
            "uncertainty": total_uncertainty
        })

        # For subsequent dilution steps
        for i in range(2, len(data) + 1):
            fdil = self.calculate_fdil(i)
            dilution_activity *= fdil['value']
            fdil_rel_unc = fdil['uncertainty'] / fdil['value']

            # Propagate the uncertainty for the subsequent dilutions
            dilution_unc = calculate_unc(dilution_unc, fdil_rel_unc)
            total_uncertainty = dilution_activity * dilution_unc
            dilution_results.append({
                "dilution_step": i,
                "value": dilution_activity,
                "uncertainty": total_uncertainty
            })

        return dilution_results
