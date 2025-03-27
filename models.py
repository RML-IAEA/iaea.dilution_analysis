from pydantic import BaseModel, Field


class Measurement(BaseModel):
    value: float = Field(..., description="Measurement value")
    uncertainty: float = Field(..., description="Measurement uncertainty")


class DilutionData(BaseModel):
    m0: Measurement
    m1: Measurement
    m2: Measurement


class DilutionCalculationResult(BaseModel):
    dilution_step: int
    value: float
    uncertainty: float
