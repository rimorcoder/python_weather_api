# Weather API (w/Redis and Docker)

Uses redis to cache requests from a weather api. Runs on docker. 

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
The first time this runs, the app will query the weather api and the response will be added to the cache then returned to the user. During testing this took around 250 ms. 
On subsequent calls the cache us referenced, which takes around 5-7 ms to respond. 
