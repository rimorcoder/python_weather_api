# Weather API
 
https://roadmap.sh/projects/weather-api-wrapper-service

## Start
Get an api token from https://www.visualcrossing.com/weather-api

Save the api token to the .env file with the following content:
```
API_KEY=your_api_key
```

Run docker compose to build and run
```
docker-compose up
```
This command is used to start the services defined in the docker-compose.yml file. It creates and starts the containers based on the configuration.

## Get Weather
Using your preferred HTTP client, run the following to get weather data, changing the path to the desired location:
```
GET http://localhost:8000/weather/new+york
```
The first time this runs, the data will be added to the cache. During testing this took around 250 ms. 
On subsequent calls, the takes around 5-7 ms. 

## Delete cached item
Run the following to remove the data from the cache
```
DELETE http://localhost:8000/weather/new+york
```
