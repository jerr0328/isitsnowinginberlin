#!/usr/bin/env python

"""
Copyright 2017 Jeremy Mayeres

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

from datetime import datetime
import os
import logging
import json
import flask
import requests
from flask_redis import FlaskRedis


# Create the application.
APP = flask.Flask(__name__)
APP.config['REDIS_URL'] = os.getenv('REDIS_URL')
redis_store = FlaskRedis(APP)
# Update delay in seconds (10 minutes)
UPDATE_DELAY_SECONDS = 600
OWM_URL = "http://api.openweathermap.org/data/2.5/weather"
OWM_FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast/daily"
OWM_HEADERS = {'x-api-key': os.getenv('OWMAPIKEY')}
OWM_PAYLOAD = {'id': 2950159}
OWM_FORECAST_PAYLOAD = {'id': 2950159, 'cnt': 2}
KELVIN = 273.15
logger = logging.getLogger('isitsnowinginberlin')


def save_current_to_redis(wx):
    wx_str = json.dumps(wx)
    with redis_store.pipeline() as pipe:
        pipe.set('cached-wx', wx_str)
        pipe.expire('cached-wx', UPDATE_DELAY_SECONDS)
        pipe.set('last-wx', wx_str)
        pipe.execute()


def save_forecast_to_redis(wx):
    wx_str = json.dumps(wx)
    with redis_store.pipeline() as pipe:
        pipe.set('cached-forecast', wx_str)
        pipe.expire('cached-forecast', UPDATE_DELAY_SECONDS)
        pipe.set('last-forecast', wx_str)
        pipe.execute()


def update_weather(update_redis=True):
    r = requests.get(OWM_URL, params=OWM_PAYLOAD, headers=OWM_HEADERS)
    r.raise_for_status()
    wx = r.json()
    if update_redis:
        save_current_to_redis(wx)
    return wx


def update_forecast(update_redis=True):
    r = requests.get(OWM_FORECAST_URL, params=OWM_FORECAST_PAYLOAD, headers=OWM_HEADERS)
    r.raise_for_status()
    wx = r.json()
    if update_redis:
        save_forecast_to_redis(wx)
    return wx


def get_weather(key='cached-wx', update_redis=True):
    cached_str = redis_store.get(key)
    if cached_str:
        logger.info("Using cached weather")
        return json.loads(cached_str)
    else:
        logger.info("Need to fetch weather")
        return update_weather(update_redis)


def get_forecast(key='cached-forecast', update_redis=True):
    cached_str = redis_store.get(key)
    if cached_str:
        logger.info("Using cached forecast")
        return json.loads(cached_str)
    else:
        logger.info("Need to fetch forecast")
        return update_forecast(update_redis)


def is_snowing(wx):
    return any("Snow" in item['main'] for item in wx['weather'])


def will_snow(forecast):
    now = datetime.now()
    return any(is_snowing(element) for element in forecast['list'] if now < datetime.fromtimestamp(element['dt']))


@APP.route('/api/flushCache')
def api_flush_cache():
    redis_store.delete('cached-wx', 'cached-forecast')
    return flask.jsonify({'success': True})


@APP.route('/api/noUpdate/rawWeather')
def api_raw_weather_no_update():
    return flask.jsonify(get_weather('last-wx', False))


@APP.route('/api/rawWeather')
def api_raw_weather():
    return flask.jsonify(get_weather())


@APP.route('/api/noUpdate/rawForecast')
def api_raw_forecast_no_update():
    return flask.jsonify(get_forecast('last-forecast', False))


@APP.route('/api/rawForecast')
def api_raw_forecast():
    return flask.jsonify(get_forecast())


@APP.route('/api/isSnowing')
def api_is_snowing():
    wx = get_weather()
    obj = {
        'isSnowing': is_snowing(wx),
        'dataUpdated': wx['dt'],
        'temperature': wx['main']['temp'] - KELVIN
    }
    return flask.jsonify(obj)


@APP.route('/api/willSnow')
def api_will_snow():
    forecast = get_forecast()
    obj = {
        'willSnow': will_snow(forecast),
        'dataUpdated': forecast['list'][1]['dt']
    }
    return flask.jsonify(obj)


@APP.route('/tomorrow/')
def tomorrow():
    """ Displays the index page accessible at '/'
    """
    return flask.send_file('tomorrow/index.html')


@APP.route('/')
def index():
    """ Displays the index page accessible at '/'
    """
    return flask.send_file('index.html')


if __name__ == '__main__':
    APP.debug = True
    APP.run()
