from pydantic import BaseModel


class NearestFloatRequest(BaseModel):
    lat: float
    lon: float
    profession: str | None = None


class NearestFloatResponse(BaseModel):
    id: str | int | None = None
    lat: float | None = None
    lon: float | None = None
    temperature: float | None = None
    salinity: float | None = None
    depth_min: float | None = None
    depth_max: float | None = None

class QueryInput(BaseModel):
    text: str

class QueryResponse(BaseModel):
    response: str