from fastapi import APIRouter
from fastapi import HTTPException
from services import DilutionService
from models import DilutionData

router = APIRouter()

service = DilutionService()


@router.post("/reset_custom_data")
async def reset_custom_data():
    """
    Reset the custom data file
    """
    service.reset_custom_data()
    return {"message": "Custom data reset successfully"}


@router.post("/set_data_source")
async def set_data_source(source: str):
    """
    Set the data source for dilution calculations
    :param source: 'default' or 'custom'
    """
    if source not in ['default', 'custom']:
        raise HTTPException(status_code=400, detail="Invalid data source")
    service.set_data_source(source)
    return {"message": f"Data source set to {source}"}


@router.post("/submit_dilution/{dilution_number}")
async def submit_dilution(dilution_number: int, dilution_data: DilutionData):
    service.set_data_source('custom')
    service.storage[dilution_number] = dilution_data
    return {"message":
            f"Dilution {dilution_number} data submitted successfully!"}

@router.get("/get_tracer/{title}")
async def get_tracer(title: str):
    return service.get_tracer(title)


@router.get("/get_tracer_by_source_id/{source_id}")
async def get_tracer_by_source_id(source_id: str):
    """
    Given a tracer source ID, return its information
    """
    return service.get_tracer_by_source_id(source_id)


@router.get("/get_tracers")
async def get_tracers():
    """
    Return a list of all tracers available in the tracer_info.json
    """
    return service.get_tracers()


@router.get("/get_dilutions")
async def get_dilutions():
    """
    Retrieve all dilution data
    """
    return service.get_dilutions()


@router.get("/calculate_net_spike/{dilution_number}")
async def calculate_net_spike(dilution_number: int):
    return service.calculate_net_spike(dilution_number)


@router.get("/calculate_net_spikes")
async def calculate_net_spikes():
    """
    Calculate net spikes for all dilution steps in data
    """
    data = await get_dilutions()
    net_spikes = []
    for dilution_number in data.keys():
        net_spike = await calculate_net_spike(int(dilution_number))
        net_spikes.append({
            "dilution_step": dilution_number,
            "net_spike": net_spike
        })
    return net_spikes


@router.get("/calculate_net_dilutant/{dilution_number}")
async def calculate_net_dilutant(dilution_number: int):
    return service.calculate_net_dilutant(dilution_number)


@router.get("/calculate_net_dilutants")
async def calculate_net_dilutants():
    """
    Calculate net dilutants for all dilution steps in data
    """
    data = await get_dilutions()
    net_dilutants = []
    for dilution_number in data.keys():
        net_dilutant = await calculate_net_dilutant(int(dilution_number))
        net_dilutants.append({
            "dilution_step": dilution_number,
            "net_dilutant": net_dilutant
        })
    return net_dilutants


@router.get("/calculate_fdil/{dilution_number}")
async def calculate_fdil(dilution_number: int):
    return service.calculate_fdil(dilution_number)


@router.get("/calculate_fdils")
async def calculate_fdils():
    """
    Calculate dilution factors for all dilution steps in data
    """
    data = await get_dilutions()
    fdils = []
    for dilution_number in data.keys():
        fdil = await calculate_fdil(int(dilution_number))
        fdils.append({
            "dilution_step": dilution_number,
            "fdil": fdil
        })
    return fdils


@router.get("/calculate_tracer_dilution/{tracer}")
async def get_tracer_dilutions(tracer):
    """
    Calculate the tracer dilution activity across multiple dilution steps
    """
    return service.calculate_tracer_dilution(tracer)
