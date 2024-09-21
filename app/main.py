from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from redis import Redis, ConnectionPool
from pydantic import BaseModel
import json
import logging
from typing import List
import httpx
import os

app = FastAPI()

# Initialize Redis connection pool
redis_pool = ConnectionPool(host='redis', port=6379, db=0)

# Initialize Redis client using the connection pool
redis_client = Redis(connection_pool=redis_pool)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class DayForecast(BaseModel):
    datetime: str
    tempmax: float
    tempmin: float
    temp: float

class WeatherData(BaseModel):
    queryCost: int
    latitude: float
    longitude: float
    resolvedAddress: str
    address: str
    timezone: str
    tzoffset: float
    days: List[DayForecast]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path
    key = f"rate_limit:{client_ip}:{endpoint}"
    rate_limit = 5  # Max requests
    time_window = 60  # Time window in seconds

    request_count = redis_client.get(key)

    if request_count is None:
        redis_client.setex(key, time_window, 1)
    else:
        request_count = int(request_count)
        if request_count < rate_limit:
            redis_client.incr(key)
        else:
            logger.warning(f"Rate limit exceeded for client: {client_ip} | {endpoint}")
            return JSONResponse(status_code=500, content={"detail": "Rate limit exceeded"})
    
    response = await call_next(request)
    return response

    
@app.get("/")
async def read_root():
    return {"message": "weather api"}

@app.get("/weather/{address}", response_model=WeatherData)
async def get_weather(address: str, request: Request):
    try:
        cached_weather = redis_client.get(f"record:{address}")

        if cached_weather:
            weather_data = json.loads(cached_weather)
            weather = WeatherData(**weather_data)
            logger.info("data retrieved from cache")  
            return weather
        else:
            api_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{address}"
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params={
                    'key': os.getenv('API_KEY'),
                    'unitGroup': 'us',
                    'include': 'current',
                    'contentType': 'json',
                    'include': 'days',
                    'elements': 'datetime,tempmax,tempmin,temp'
                })
                    

            response.raise_for_status()  # Raise an exception for HTTP errors
            weather_data = response.json()
            weather = WeatherData(**weather_data)
            redis_client.set(f"record:{address}", json.dumps(weather.dict())) 
            logger.info("data added to cache")  
            return weather
    except Exception as e:
        logger.error(e, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    
@app.delete("/weather/{address}")
async def delete_weather(address: str, request: Request):
    redis_client.delete(f"record:{address}")
    logger.info("data deleted from cache")  
    return {"message": f"{address} deleted from cache."}