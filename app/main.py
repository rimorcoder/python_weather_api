from fastapi import FastAPI, Request
from redis import Redis
from pydantic import BaseModel
import json
import logging
from typing import List
import requests
import os
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# rate limits
async def rate_limit_exceeded(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )
def get_client_ip(request: Request) -> str:
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0]
    return request.client.host
limiter = Limiter(key_func=get_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded)
app.add_middleware(SlowAPIMiddleware)

# Connect to Redis
redis_client = Redis(host='redis', port=6379, db=0)

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

@limiter.limit("5/minute") 
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
        response = requests.get(api_url, params={'key':os.getenv('API_KEY'),
                                                 'unitGroup':'us',
                                                 'include':'current',
                                                 'contentType':'json',
                                                 'include':'days',
                                                 'elements':'datetime,tempmax,tempmin,temp'
                                                 })
        

        response.raise_for_status()  # Raise an exception for HTTP errors
        weather_data = response.json()
        weather = WeatherData(**weather_data)
        redis_client.set(f"record:{address}", json.dumps(weather.dict())) 
        logger.info("data added to cache")  
        return weather
    
@limiter.limit("5/minute") 
@app.delete("/weather/{address}")
async def delete_weather(address: str, request: Request):
    redis_client.delete(f"record:{address}")
    logger.info("data deleted from cache")  
    return {"message": f"{address} deleted from cache."}