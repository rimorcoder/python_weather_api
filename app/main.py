from fastapi import FastAPI, Request, Depends
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

@app.get("/")
async def read_root():
    return {"message": "weather api"}

@app.get("/weather/{address}", response_model=WeatherData)
async def get_weather(address: str, request: Request):
    cached_weather = redis_client.get(f"record:{address}")

    if cached_weather:
        weather_data = json.loads(cached_weather)
        weather = WeatherData(**weather_data)
        logger.info("data retrieved from cache")  
        return weather
    else:
        api_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{address}"
        response = httpx.get(api_url, params={
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
    
@app.delete("/weather/{address}")
async def delete_weather(address: str, request: Request):
    redis_client.delete(f"record:{address}")
    logger.info("data deleted from cache")  
    return {"message": f"{address} deleted from cache."}