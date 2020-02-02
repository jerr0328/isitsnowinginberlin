#!/usr/bin/env python

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

import json
import logging
import os
from datetime import datetime

import flask
import requests
from flask_redis import FlaskRedis

# Create the application.
APP = flask.Flask(__name__)
APP.config["REDIS_URL"] = os.getenv("REDIS_URL")
redis_store = FlaskRedis(APP)
# Update delay in seconds (10 minutes)
UPDATE_DELAY_SECONDS = 600
DARKSKY_URL = "https://api.darksky.net/forecast/{key}/{coords}".format(
    key=os.getenv("DARKSKY_KEY"), coords="52.52,13.37"
)
DARKSKY_PAYLOAD = {"units": "si", "exclude": "[minutely,hourly,flags,alerts]"}

logger = logging.getLogger("isitsnowinginberlin")


def save_current_to_redis(wx):
    wx_str = json.dumps(wx)
    with redis_store.pipeline() as pipe:
        pipe.set("cached-wx", wx_str)
        pipe.expire("cached-wx", UPDATE_DELAY_SECONDS)
        pipe.set("last-wx", wx_str)
        pipe.execute()


def update_weather(update_redis=True):
    r = requests.get(DARKSKY_URL, params=DARKSKY_PAYLOAD)
    r.raise_for_status()
    wx = r.json()
    if update_redis:
        save_current_to_redis(wx)
    return wx


def get_weather(key="cached-wx", update_redis=True):
    cached_str = redis_store.get(key)
    if cached_str:
        logger.info("Using cached weather")
        return json.loads(cached_str)
    else:
        logger.info("Need to fetch weather")
        return update_weather(update_redis)


def is_snowing(wx):
    return wx["currently"]["icon"] == "snow"


def will_snow(wx):
    now = datetime.now()
    next_forecast = next(
        data
        for data in wx["daily"]["data"]
        if now < datetime.fromtimestamp(data["time"])
    )
    return next_forecast["icon"] == "snow"


@APP.route("/api/flushCache")
def api_flush_cache():
    redis_store.delete("cached-wx")
    return flask.jsonify({"success": True})


@APP.route("/api/noUpdate/rawWeather")
def api_raw_weather_no_update():
    return flask.jsonify(get_weather("last-wx", False))


@APP.route("/api/rawWeather")
def api_raw_weather():
    return flask.jsonify(get_weather())


@APP.route("/api/isSnowing")
def api_is_snowing():
    wx = get_weather()
    obj = {
        "isSnowing": is_snowing(wx),
        "dataUpdated": wx["currently"]["time"],
        "temperature": wx["currently"]["temperature"],
    }
    return flask.jsonify(obj)


@APP.route("/api/willSnow")
def api_will_snow():
    wx = get_weather()
    obj = {"willSnow": will_snow(wx), "dataUpdated": wx["currently"]["time"]}
    return flask.jsonify(obj)


@APP.route("/tomorrow/")
def tomorrow():
    """ Displays the index page accessible at '/'
    """
    return flask.send_file("tomorrow/index.html")


@APP.route("/")
def index():
    """ Displays the index page accessible at '/'
    """
    return flask.send_file("index.html")


if __name__ == "__main__":
    APP.debug = True
    APP.run()
