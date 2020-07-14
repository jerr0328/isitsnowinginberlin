"""
Copyright 2020 Jeremy Mayeres

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import asyncio
import json
import logging
import os
from datetime import datetime

import aioredis
import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_camelcase import CamelModel

logging.basicConfig()
logger = logging.getLogger("isitsnowinginberlin")
app = FastAPI()

BERLIN_COORDS = "52.52,13.37"
UPDATE_DELAY_SECONDS = 600  # Update delay in seconds (10 minutes)
DARKSKY_URL = (
    f"https://api.darksky.net/forecast/{os.getenv('DARKSKY_KEY')}/{BERLIN_COORDS}"
)
DARKSKY_PAYLOAD = {"units": "si", "exclude": "[minutely,hourly,flags,alerts]"}
REDIS_URL = os.getenv("REDIS_URL")
CACHE_KEY = "cached-wx"


class SnowingResponse(CamelModel):
    is_snowing: bool
    data_updated: int
    temperature: float


class WillSnowResponse(CamelModel):
    will_snow: bool
    data_updated: int


async def store_weather(wx: dict):
    logger.info("Updating cache")
    wx_str = json.dumps(wx)
    await app.redis.set(CACHE_KEY, wx_str, expire=UPDATE_DELAY_SECONDS)


async def update_weather() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(DARKSKY_URL, params=DARKSKY_PAYLOAD)
        r.raise_for_status()
        wx = r.json()
        asyncio.create_task(store_weather(wx))
        return wx


async def get_weather() -> dict:
    cached_str = await app.redis.get(CACHE_KEY, encoding="utf-8")
    if cached_str:
        logger.info("Using cached weather")
        return json.loads(cached_str)
    else:
        logger.info("Need to fetch weather")
        return await update_weather()


def is_snowing(wx: dict) -> bool:
    return wx["currently"]["icon"] == "snow"


def will_snow(wx: dict) -> bool:
    now = datetime.now()
    next_forecast = next(
        data
        for data in wx["daily"]["data"]
        if now < datetime.fromtimestamp(data["time"])
    )
    return next_forecast["icon"] == "snow"


@app.on_event("startup")
async def setup():
    app.redis = await aioredis.create_redis_pool(REDIS_URL)


@app.get("/api/rawWeather")
async def api_raw_weather():
    return await get_weather()


@app.get("/api/isSnowing", response_model=SnowingResponse)
async def api_is_snowing():
    wx = await get_weather()
    return {
        "isSnowing": is_snowing(wx),
        "dataUpdated": wx["currently"]["time"],
        "temperature": wx["currently"]["temperature"],
    }


@app.get("/api/willSnow", response_model=WillSnowResponse)
async def api_will_snow():
    wx = await get_weather()
    return {"willSnow": will_snow(wx), "dataUpdated": wx["currently"]["time"]}


@app.get("/tomorrow/")
async def tomorrow():
    return FileResponse("tomorrow/index.html")


@app.get("/")
async def main():
    return FileResponse("index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
